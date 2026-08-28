import numpy as np
import nibabel as nib
import torch
from scipy.ndimage import zoom
from scipy import ndimage
from monai.networks.nets import UNet
from monai.inferers import sliding_window_inference

dev = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# ---------- priprema snimaka ----------
def ucitaj_na_1mm(putanja, je_maska=False):
    img = nib.load(putanja)
    d = img.get_fdata()
    d = zoom(d, np.array(img.header.get_zooms()[:3])/1.0, order=0 if je_maska else 1)
    return (d > 0.5).astype(np.float32) if je_maska else d

def normalizuj(s):
    mozak = s[s > 0]
    p1, p99 = np.percentile(mozak, [1, 99])
    s = np.clip(s, p1, p99)
    s = (s - p1) / (p99 - p1 + 1e-8)
    return s.astype(np.float32)

# ---------- ucitavanje modela ----------
def ucitaj_model(putanja, in_channels, channels=(16,32,64,128,256)):
    model = UNet(spatial_dims=3, in_channels=in_channels, out_channels=1,
                 channels=channels, strides=(2,2,2,2), num_res_units=2).to(dev)
    model.load_state_dict(torch.load(putanja, map_location=dev))
    model.eval()
    return model

# ---------- predikcija: sve lezije (Deo 1, jedan snimak) ----------
def predvidi_sve_lezije(model, flair_putanja, prag=0.5):
    s = normalizuj(ucitaj_na_1mm(flair_putanja))
    x = torch.tensor(s[np.newaxis, np.newaxis].astype(np.float32)).to(dev)
    with torch.no_grad():
        o = sliding_window_inference(x, (64,64,64), 4, model, overlap=0.25)
        pred = torch.sigmoid(o).cpu().numpy()[0,0]
    return s, pred > prag   # vraca i snimak (za prikaz) i masku lezija

# ---------- predikcija: nove lezije (Deo 2, dva snimka) ----------
def predvidi_nove_lezije(model, flair1_putanja, flair2_putanja, prag=0.5):
    s1 = normalizuj(ucitaj_na_1mm(flair1_putanja))
    s2 = normalizuj(ucitaj_na_1mm(flair2_putanja))
    ms = [min(s1.shape[i], s2.shape[i]) for i in range(3)]
    s1, s2 = s1[:ms[0],:ms[1],:ms[2]], s2[:ms[0],:ms[1],:ms[2]]
    x = torch.tensor(np.stack([s1,s2],0)[np.newaxis].astype(np.float32)).to(dev)
    with torch.no_grad():
        o = sliding_window_inference(x, (64,64,64), 4, model, overlap=0.25)
        pred = torch.sigmoid(o).cpu().numpy()[0,0]
    return s1, s2, pred > prag

# ---------- merenje lezija ----------
def izmeri_lezije(maska):
    lbl, broj = ndimage.label(maska)
    if broj == 0:
        return 0, 0, 0, []
    velicine = ndimage.sum(maska, lbl, range(1, broj+1))
    velicine = sorted([int(v) for v in velicine], reverse=True)
    ukupno = sum(velicine)         # mm3 (1mm rezolucija -> 1 tacka = 1 mm3)
    najveca = velicine[0]
    return broj, ukupno, najveca, velicine