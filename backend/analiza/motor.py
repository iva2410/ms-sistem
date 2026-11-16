"""Segmentacija nnU-Net modelima.

Model se ucitava iz foldera backend/modeli/<Dataset...>/ (plans.json, dataset.json,
fold_0/checkpoint_final.pth). Mreza se gradi direktno iz plans.json, pa nisu potrebne
posebne trener klase koriscene u obuci.
"""
import json
import threading
from pathlib import Path

import konfiguracija as kfg

_kes = {}
_brava = threading.Lock()


def pronadji_model(kljuc: str):
    """Vraca (folder_modela, putanja_checkpointa) ili None ako model nije instaliran."""
    naziv_skupa = kfg.MODELI_REGISTAR[kljuc][0]
    koren = kfg.MODELI / naziv_skupa
    if not koren.is_dir():
        return None
    for plans in sorted(koren.rglob('plans.json')):
        folder = plans.parent
        if not (folder / 'dataset.json').exists():
            continue
        for ime in ('checkpoint_final.pth', 'checkpoint_best.pth'):
            ck = folder / 'fold_0' / ime
            if ck.exists():
                return folder, ck
    return None


def stanje_modela():
    """Pregled instaliranih modela za stranicu Sistem."""
    lista = []
    for kljuc, (skup, opis, kanala) in kfg.MODELI_REGISTAR.items():
        nadjen = pronadji_model(kljuc)
        lista.append({
            'kljuc': kljuc, 'opis': opis, 'folder': skup, 'kanala': kanala,
            'instaliran': nadjen is not None,
            'checkpoint': nadjen[1].name if nadjen else None,
        })
    return lista


def uredjaj():
    import torch
    if kfg.UREDJAJ == 'auto':
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    return torch.device(kfg.UREDJAJ)


def opis_uredjaja():
    try:
        import torch
        if uredjaj().type == 'cuda':
            return 'GPU ({})'.format(torch.cuda.get_device_name(0))
        return 'CPU'
    except Exception:
        return 'PyTorch nije instaliran'


def _ucitaj(kljuc: str):
    if kljuc in _kes:
        return _kes[kljuc]
    import torch
    from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
    from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import nnUNetTrainer
    from nnunetv2.utilities.label_handling.label_handling import determine_num_input_channels
    from nnunetv2.utilities.plans_handling.plans_handler import PlansManager

    nadjen = pronadji_model(kljuc)
    if nadjen is None:
        raise RuntimeError('Model „{}” nije instaliran (folder modeli/{}).'.format(
            kfg.MODELI_REGISTAR[kljuc][1], kfg.MODELI_REGISTAR[kljuc][0]))
    folder, ck_putanja = nadjen
    dataset_json = json.loads((folder / 'dataset.json').read_text(encoding='utf-8'))
    plans = json.loads((folder / 'plans.json').read_text(encoding='utf-8'))
    ck = torch.load(str(ck_putanja), map_location=torch.device('cpu'), weights_only=False)

    plans_manager = PlansManager(plans)
    konfig = plans_manager.get_configuration(ck['init_args']['configuration'])
    n_ulaz = determine_num_input_channels(plans_manager, konfig, dataset_json)
    n_izlaz = plans_manager.get_label_manager(dataset_json).num_segmentation_heads
    mreza = nnUNetTrainer.build_network_architecture(
        plans_manager, konfig, n_ulaz, n_izlaz, enable_deep_supervision=False)
    mreza.load_state_dict(ck['network_weights'])

    dev = uredjaj()
    na_gpu = dev.type == 'cuda'
    prediktor = nnUNetPredictor(
        tile_step_size=0.5, use_gaussian=True,
        use_mirroring=na_gpu,                 # na CPU bez ogledanja: ~8 puta brze
        perform_everything_on_device=na_gpu, device=dev,
        verbose=False, verbose_preprocessing=False, allow_tqdm=False)
    prediktor.manual_initialization(
        mreza, plans_manager, konfig, [ck['network_weights']], dataset_json,
        ck.get('trainer_name', 'nnUNetTrainer'), ck.get('inference_allowed_mirroring_axes'))
    _kes.clear()                              # u memoriji drzimo samo jedan model
    _kes[kljuc] = (prediktor, plans_manager, konfig, dataset_json, n_ulaz, ck_putanja.name)
    return _kes[kljuc]


def segmentuj(kljuc: str, kanali, izlaz_dir):
    """Pokrece model nad jednim slucajem.

    kanali: lista putanja NIfTI fajlova (po jedan za svaki ulazni kanal, ista geometrija).
    Vraca (putanja_maske, putanja_verovatnoce, info). Verovatnoca je sacuvana kao 0-255.
    """
    import numpy as np
    import torch
    from nnunetv2.inference.export_prediction import (
        convert_predicted_logits_to_segmentation_with_correct_shape)

    izlaz_dir = Path(izlaz_dir)
    izlaz_dir.mkdir(parents=True, exist_ok=True)
    with _brava:
        prediktor, plans_manager, konfig, dataset_json, n_ulaz, ck_ime = _ucitaj(kljuc)
        if len(kanali) != n_ulaz:
            raise RuntimeError('Model očekuje {} ulaznih snimaka, dobijeno {}.'.format(n_ulaz, len(kanali)))
        pretprocesor = konfig.preprocessor_class(verbose=False)
        podaci, _, svojstva = pretprocesor.run_case(
            [str(k) for k in kanali], None, plans_manager, konfig, dataset_json)
        logiti = prediktor.predict_logits_from_preprocessed_data(torch.from_numpy(podaci)).cpu()
        seg, verov = convert_predicted_logits_to_segmentation_with_correct_shape(
            logiti, plans_manager, konfig, prediktor.label_manager, svojstva,
            return_probabilities=True)
        pisac = plans_manager.image_reader_writer_class()
        zavrsetak = dataset_json.get('file_ending', '.nii.gz')
        maska_p = izlaz_dir / ('maska' + zavrsetak)
        verov_p = izlaz_dir / ('verovatnoca' + zavrsetak)
        pisac.write_seg(seg.astype(np.uint8), str(maska_p), svojstva)
        v8 = np.clip(np.round(verov[1] * 254.0), 0, 254).astype(np.uint8)
        pisac.write_seg(v8, str(verov_p), svojstva)
    info = {'model': kfg.MODELI_REGISTAR[kljuc][1], 'folder': kfg.MODELI_REGISTAR[kljuc][0],
            'checkpoint': ck_ime, 'uredjaj': opis_uredjaja()}
    return maska_p, verov_p, info
