# AMES boru hattı — kullanılan 21 notebook

Makalenin dayandığı kod. 41 notebook'luk koleksiyondan ayıklandı; kopyalar ve hata ile durmuş
denemeler `archive/` klasöründe.

Orijinal parça numaraları korundu. Notebook'lar metin içinde birbirine "Part 17", "Parts 2 to 5"
diye atıf yapıyor; numaralar değişirse o atıflar kopar.

## Doğrulama

Üç bağımsız nokta makaledeki sayılarla karşılaştırıldı ve tuttu:

| Notebook | Kontrol | Sonuç |
|---|---|---|
| `part01` | Tablo S2 validasyon ROC-AUC | 0.8389 / 0.8335 / 0.8493 / 0.8519 / 0.8466 — birebir |
| `part01` | Tablo S1 designated partition | 7255 bileşik; 5804 / 725 / 726; %55,6 / %53,7 / %46,3 — birebir |
| `part10` | Çapraz doğrulama ROC-AUC | 0.8320 / 0.8209 / 0.8450 / 0.8430 / 0.8450 / 0.8540 — birebir |
| `part17` | `rep201/202/203_degree_auroc` | 0.6070 / 0.5712 / 0.5360 — ledger ile aynı |
| `part19` | `opt_family_gap`, `dodrep201` | −0.0267, −0.0887 — ledger ile aynı |

Birincil bölünme `PRIMARY_SPLIT_SEED = 101` ile kuruluyor ve bu seed boru hattının tamamında
tutarlı. (`archive/` içindeki seed 47 kullanan notebook'lar hiç çalıştırılmamış.)

## Ortam

**Sürümler sabitlenmemiş.** Notebook'ların hepsi `pip install rdkit` ve
`pip install torch_geometric` diye kurulum yapıyor, sürüm belirtmeden. Kayda geçmiş tek
ortam `part19`'unki:

```
rdkit 2026.03.5
torch_geometric 2.8.0
```

Bu bir risk: kanonik SMILES, Murcko scaffold'ları ve `state_dict` anahtar adları sürüme
duyarlı. Depoya yüklemeden önce çalışan sürümlerin `pip freeze` ile kaydedilip
sabitlenmesi gerekiyor.

Çalışma dizini: `/content/drive/MyDrive/ames_pipeline` — altında `data/`, `results/`,
`explain/`, `models/`, `ckpt/`, `figures/` klasörleri.

`part01` veriyi internetten **indirmiyor**: `data/` klasöründe `train.csv`, `valid.csv` ve
`test.csv` dosyalarının hazır bulunmasını bekliyor ve yoksa hata veriyor. Bu üç dosya
Therapeutics Data Commons'ın Ames benchmark'ından geliyor.

Diğer notebook'lar `ames9.py` ortak tanım dosyasını `%%writefile` ile kendileri üretiyor,
ayrıca kurulum gerekmiyor.

## Çalıştırma sırası

Boru hattı kendi kendine yeterli: dışarıdan hiçbir dosya gerekmiyor, her notebook'un okuduğu
her dosyayı önceki bir notebook üretiyor.

| # | Notebook | Önce çalışması gerekenler |
|---|---|---|
| 1 | `part01_data_and_hpo` | — |
| 2 | `part02_models` | 01 |
| 3 | `part03_benchmark` | 01 |
| 4 | `part04_attribution` | 01 |
| 5 | `part04b_corrections` | 01, 04 |
| 6 | `part05_robustness` | 01, 02, 03, 04 |
| 7 | `part07_structural` | 04 |
| 8 | `part08_structural_baselines` | 01, 02, 04, 05 |
| 9 | `part09_multimodel` | 01, 02, 05 |
| 10 | `part09b_masks_and_curve` | 01, 02, 05 |
| 11 | `part10_crossvalidation` | 01, 03, 05, 08 |
| 12 | `part12_architectures_intervals` | 01, 02, 04, 09 |
| 13 | `part13_encoding_ablation` | 01, 02, 12 |
| 14 | `part14_paired_comparison` | 02, 04, 08, 12 |
| 15 | `part15_regime_intervals` | 02 |
| 16 | `part16_threshold_free` | 01, 02, 03, 08, 12 |
| 17 | `part17_partition_replication` | 01, 02, 04, 09 |
| 18 | `part18_decision_rules` | 01, 02 |
| 19 | `part19_own_standard` | 01, 02, 10 |
| 20 | `part06_figures` | 01, 02, 03, 04, 04b, 05 |
| 21 | `part11_manuscript_assets` | 01, 02, 04, 04b, 05, 07, 08, 09, 09b, 10 |

`part06` ve `part11` şekilleri ve `.tex` tablolarını üretir, en sona bırakılır.

## Ledger nasıl toplanıyor

Makaledeki `manuscript_numbers.csv` 854 satır, ama tek bir notebook'tan çıkmıyor:

- `part06` → 51 nicelik
- `part11` → 19 nicelik, ayrıca `.tex` tablo parçaları
- `part16` → `table85_part16_ledger.csv`, 140 nicelik
- `part17` → `table91_part17_ledger.csv`, 77 nicelik
- `part18` → `table95_part18_ledger.csv`
- `part19` → `table100_part19_ledger.csv`

Bunlar birleştirilerek nihai ledger elde ediliyor. Yeniden üretirken bu birleştirme adımının
atlanmaması gerekiyor, yoksa `check_consistency.py` metindeki sayıların çoğunu eşleşmemiş
sayar.

## Gönderim öncesi açık kalan dört madde

1. Makale "eleven notebooks" diyor (`main.tex` satır 349, `supporting.tex` "Code and data").
   Elde 21 notebook var. Ya birleştirilecek ya da sayı düzeltilecek.
2. `main.tex` satır 921'de `[repository URL]` ve `[Zenodo DOI]` hâlâ placeholder.
3. `part17` çıktısında `table88_regimes_by_partition.csv: stage could not run, not cached`
   uyarısı var. Sayılar ekrana basılmış ama diske yazılmamış; `cached()` yardımcısı "note"
   sütunu dolu tabloyu yazmayı reddediyor. Makalede bu tablodan gelen bir sayı varsa
   kaynağı kontrol edilmeli.
4. `train_gnn` fonksiyonu `pos_weight` parametresi alıyor, oysa makale eğitimin ağırlıksız
   kayıpla yapıldığını söylüyor (`main.tex` satır 228). `part02` ve `part10`'da bu fonksiyonun
   nasıl çağrıldığı doğrulanmalı.
