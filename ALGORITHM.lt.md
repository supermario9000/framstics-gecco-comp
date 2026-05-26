# SouperTeam — Kodėl `algorithm.py` yra pranašesnis už pavyzdį

Šis dokumentas konkrečiais moksliniais ir matematiniais terminais paaiškina,
kodėl [algorithm.py](algorithm.py) (adaptyvus daugiastrateginis evoliucinis
algoritmas, toliau **AMS-EA**) tikėtinai pranoks pavyzdinį atskaitos
algoritmą [FramsticksEvolution.py](FramsticksEvolution.py) (DEAP biblioteka
paremtas `eaSimple` su fiksuotais parametrais, toliau **eaSimple**) GECCO
Framsticks svorio centro (COG) trajektorijos uždavinyje.

Argumentas sustyguotas aplink aštuonis nepriklausomus patobulinimus. Kiekvienas
iš jų yra pagrįstas žinomu rezultatu iš evoliucinio skaičiavimo literatūros,
ir kiekvienas taikinas konkrečiam `eaSimple` algoritmo gedimo režimui šiame
uždavinyje.

---

## 1. Stiprus (μ + λ) elitizmas vs. kartų pakeitimas

**Atskaita.** `eaSimple` atlieka *kartinį* pakeitimą
([FramsticksEvolution.py:232](FramsticksEvolution.py#L232)):

```python
pop[:] = offspring
```

Palikuonių populiacija *visiškai pakeičia* tėvus. Geriausias kada nors
kartoje rastas individas gali būti prarastas kitoje kartoje, jei kryžminimas
ir mutacija jį suprastina. Šlovės salė (Hall-of-Fame) yra tik *fiksuojama*,
o ne grąžinama atgal.

**AMS-EA.** Mes naudojame (μ + λ) elitinį pakeitimą
([algorithm.py:404-420](algorithm.py#L404-L420)): tėvų ir palikuonių
sąjunga rūšiuojama pagal tinkamumą ir geriausi `μ` išlieka. Be to,
geriausi 15 % populiacijos garantuotai išlieka kiekvienoje kartoje
([algorithm.py:36](algorithm.py#L36)).

**Kodėl tai svarbu.** Rudolph (1994) įrodė, kad elitinis EA baigtinėje
diskrečioje paieškos erdvėje su tikimybe 1 konverguoja į globalų
optimumą, o neelitiniai EA tokios garantijos neturi. Triukšmingame /
apgaulingame kraštovaizdyje, tokiame kaip COG-kelio tinkamumas, geriausio
nugalėtojo praradimas dėl vienos blogos mutacijos gali ištrinti dešimtis
tūkstančių vertinimų pažangos. Stiprus elitizmas paverčia geriausią-iki-šiol
monotoniškai nemažėjančia seka:

    f*(t+1) ≥ f*(t)   visoms kartoms t

Tai netiesa `eaSimple` atveju.

---

## 2. Adaptyvūs operatorių dažniai pagal stebimą sėkmę

**Atskaita.** `pmut = 0.9` ir `pxov = 0.2` yra fiksuoti komandinėje
eilutėje ir niekada neatnaujinami
([FramsticksEvolution.py:146-147](FramsticksEvolution.py#L146-L147)).
Jie parinkti *a priori* ir lieka pastovūs per visus 10 konkurso nustatymus,
nors tinkamumo kraštovaizdžiai yra skirtingi.

**AMS-EA.** Operatorių dažniai atnaujinami internetiniu būdu naudojant
nuopelnų priskyrimo taisyklę
([algorithm.py:229-251](algorithm.py#L229-L251)). Kiekvienam operatoriui
*op ∈ {mutacija, kryžminimas}* palaikome bandymų ir sėkmių skaitiklius;
palikuonis laikomas sėkme, jei jo tinkamumas viršija populiacijos
*medianą*. Kas 20 bandymų atnaujiname:

    s = sėkmės / bandymai
    jei s > τ_aukšta:  dažnis ← min(dažnis_max, dažnis + 0.02)
    jei s < τ_žema:    dažnis ← max(dažnis_min, dažnis − 0.02)

su `τ_aukšta = 0.25, τ_žema = 0.10` mutacijai, ir rėžiais
`[0.40, 0.95]`, kad dažnis niekada nesusiglaustų ir nepasisotintų.

**Kodėl tai svarbu.** Tai yra **adaptyvaus operatorių parinkimo** (AOS)
forma, gerai studijuota nuo Davis (1989) ir formalizuota Fialho ir kt.
(2010). Uždaviniuose, kur santykinis mutacijos ir kryžminimo naudingumas
kinta vykdymo metu (tipiškai: tyrimas pradžioje, eksploatavimas pabaigoje),
adaptyvūs dažniai dominuoja prieš bet kokį aklai parinktą fiksuotą grafiką.
Mediana paremtas atlygis išvengia *kartos geriausiojo* atlygio šališkumo
(kuris pernelyg vertina sėkmingus pagerinimus).

---

## 3. Stagnacijos aptikimas ir dalinis perkrovimas

**Atskaita.** `eaSimple` *neturi* perkrovimo mechanizmo. Jei populiacija
konverguoja į lokalų optimumą 3-iojoje kartoje, ji ir toliau mutuos aplink
tą optimumą visoms likusioms kartoms. Įvairovė, matuojama, pvz., genotipo
Hamming atstumu, monotoniškai krenta.

**AMS-EA.** Kai geriausias tinkamumas nepagerėja per
`STAGNATION_WINDOW = 15` kartas
([algorithm.py:46](algorithm.py#L46)), suaktyviname *dalinį perkrovimą*
([algorithm.py:260-287](algorithm.py#L260-L287)):

1. Išlaikome elitą (top 15 %) — išsaugome tai, ką žinome.
2. Pridedame iki 5 mutuotų Šlovės salės narių kopijų — tyrinėjame
   istoriškai gerų baseinų apylinkes.
3. Užpildome likusią dalį (~40 % populiacijos) nauja, įvairia sėkla —
   įpurškiame tyrinėjimo entropijos.

**Kodėl tai svarbu.** Tai įgyvendina **atsitiktinius imigrantus**
(Grefenstette 1992) kartu su **CHC-stiliaus perkrovimu** (Eshelman 1991).
Matematiškai tai padidina pagrindinės Markovo grandinės maišymosi laiką
genotipo erdvėje, iš apačios apribodama tikimybę ištrūkti iš bet kurio
traukos baseino per baigtinį horizontą. Esant 100 tūkst. vertinimų biudžetui
su daugeliu lokaliųjų optimumų, tai skiriasi tarp vieno baseino tyrimo ir
kelių.

---

## 4. Šlovės salės *atgalinis įpurškimas* (ne tik fiksavimas)

**Atskaita.** DEAP'o `HallOfFame` yra pasyvus žurnalas: jis seka geriausius
N kada nors matytus individus, bet niekada negrąžina jų į populiaciją
([FramsticksEvolution.py:210, 233](FramsticksEvolution.py#L210)).

**AMS-EA.** Kas 10 kartų pakeičiame blogiausią dabartinį individą
*mutuotu* Šlovės salės nariu
([algorithm.py:422-428](algorithm.py#L422-L428)). Perkrovimų metu sėjame
iki 5 mutuotų HoF narių
([algorithm.py:273-278](algorithm.py#L273-L278)).

**Kodėl tai svarbu.** Tai paverčia paiešką naudingai ne-markoviška:
istoriškai geri regionai gali būti aplankyti pakartotinai net po to, kai
populiacija nutolo nuo jų. Tai yra baigtinės atminties aproksimacija
*archyvais paremtų* metodų (NSGA-II archyvai, MAP-Elites tinkleliai),
kurie nuosekliai pranoksta atminties neturinčius EA.

---

## 5. Biudžetą suvokiantis vertinimų skaičiavimas

**Atskaita.** `eaSimple` parametrizuojamas *kartomis*
([FramsticksEvolution.py:144](FramsticksEvolution.py#L144), numatytasis 5).
Faktinis vertinimų skaičius yra `popsize × (generations + 1)`. Jei
naudotojas neteisingai nustato dydį, algoritmas arba sustoja gerokai
nepasiekęs 100 000 biudžeto (švaisto vertinimus), arba, blogiau, viršija
realaus laiko ribą ir nužudomas vidury kartos.

**AMS-EA.** Pagrindinis ciklas sąlygoja likusiais vertinimais, o ne
kartomis ([algorithm.py:207-211, 329-334](algorithm.py#L207-L211)):

    likęs_biudžetas = MAX_EVALUATIONS − SAFETY_MARGIN − total_evaluations

Paketo dydis grakščiai mažėja, biudžetui senkant
([algorithm.py:331-336](algorithm.py#L331-L336)), o 500 vertinimų saugos
atsarga užtikrina, kad niekada nesuaktyvinsime simuliatoriaus griežto
nužudymo vidury vykdymo.

**Kodėl tai svarbu.** Konkursas normalizuoja balus per vienodo biudžeto
vykdymus. Algoritmas, panaudojantis 98 000 iš 100 000 vertinimų, visada
silpnai dominuoja tą, kuris sustoja ties 50 000. Biudžetą suvokiantis
dydžio nustatymas garantuoja, kad išgausime kiekvieną vertinimą, į kurį
turime teisę.

---

## 6. Įvairi inicializacija

**Atskaita.** Kiekvienas individas yra *tas pats* paprasčiausias genotipas,
sukurtas `getSimplest()`
([FramsticksEvolution.py:66, 119](FramsticksEvolution.py#L66)). Pradinė
populiacija turi nulinę įvairovę — visi 50 individų yra identiški. Pirmoji
mutacijų karta yra vienintelis variacijos šaltinis.

**AMS-EA.** Mes pasodiname kiekvieną individą, taikydami *atsitiktinį
skaičių* mutacijų (paimtų iš `{1,2,3,4,5,6}`) paprasčiausiam genotipui
([algorithm.py:120-134](algorithm.py#L120-L134)). Pradinės populiacijos
tikėtinas porinis Hamming atstumas todėl yra griežtai teigiamas, vienu
metu apimantis kelis sudėtingumo lygius.

**Kodėl tai svarbu.** Populiacijos įvairovė momentu *t = 0* dominuoja
asimptotinį bet kurio EA su baigtine perkrovimo tikimybe elgesį. Pradėti
nuo 50 klonų reiškia, kad pirmosios 1–2 kartos praleidžiamos atkuriant
įvairovę, kuri turėjo būti nuo pat pradžių — grynas vertinimo biudžeto
švaistymas.

---

## 7. Hibridinis turnyro + rango paremtas parinkimas

**Atskaita.** Grynas turnyro parinkimas su fiksuotu `tournsize = 5`
([FramsticksEvolution.py:126](FramsticksEvolution.py#L126)). Turnyro
parinkimas turi pastovų parinkimo spaudimą, nepriklausomai nuo tinkamumo
pasiskirstymo: jei visi individai beveik vienodi, nugalėtojas yra iš
esmės atsitiktinis (gerai); jei vienas yra dramatiškai geresnis, jis
dominuoja kiekviename savo turnyre (blogai — ankstyva konvergencija).

**AMS-EA.** Mes maišome dvi parinkimo schemas su 70/30 santykiu
([algorithm.py:355-361](algorithm.py#L355-L361)): turnyras-5 (didelis
spaudimas, geras eksploatavimui) ir linijinis rangavimas (mažas spaudimas,
įvairovę išsaugantis). Linijinis rangavimas priskiria parinkimo tikimybę

    p_i = rang_i / Σ rang

taigi net blogiausias tinkamas individas turi nenulinę galimybę būti
parinktas — išsaugant genetinę medžiagą, kuri gali rekombinuotis į
ateities proveržį.

**Kodėl tai svarbu.** Goldberg & Deb (1991) parodė, kad jokia atskira
parinkimo schema nėra visuotinai geriausia. Mišinys sumažina dispersiją
per kraštovaizdžius, kas tiesiogiai pagerina *vidurkintą* balą per 10
konkurso nustatymus.

---

## 8. Daugkartinės mutacijos gylis esant stagnacijai

**Atskaita.** Vienas `mutate()` iškvietimas per palikuonį
([FramsticksEvolution.py:61](FramsticksEvolution.py#L61)). Tikėtinas
fenotipinis žingsnio dydis yra fiksuotas visam vykdymui.

**AMS-EA.** Kai aptinkama stagnacija, mutacijos gylis padidėja iki 4
nuoseklių mutacijų vienam palikuoniui
([algorithm.py:253-258, 137-146](algorithm.py#L253-L258)):

    gylis = min(MAX_MUTATION_DEPTH, 1 + kartos_be_pagerėjimo / (W/2))

Tai atitinka didesnio žingsnio darymą genotipo erdvėje, kai lokalios
gradiento informacijos atsargos yra išsemtos.

**Kodėl tai svarbu.** Tai yra diskretus **CMA-ES žingsnio dydžio
kontrolės** analogas (Hansen 2001): kai pažanga sustoja, didinkite
paieškos spindulį; kai pažanga atsinaujina, susitraukinkite. Vienos
mutacijos atskaita negali ištrūkti iš lokalių optimumų, kuriems reikia
koordinuoto daugiagenio pakeitimo.

---

## Bendras poveikis konkurso tikslui

Konkurso balas yra

    balas = (1/10) Σ_s normalizuoti_s( vidurkis per 20 pakartojimų
                                         geriausio tinkamumo )

Norint laimėti, algoritmas turi pateikti *aukštą vidutinį geriausią
tinkamumą su maža dispersija* per heterogeniškus nustatymus. Aštuonios
aukščiau išvardintos savybės puola šį tikslą iš papildomų krypčių:

| Patobulinimas                  | Mažina dispersiją | Kelia vidurkį |
|--------------------------------|:-----------------:|:-------------:|
| 1. Elitizmas                   | ✅                | ✅            |
| 2. Adaptyvūs dažniai           |                   | ✅            |
| 3. Stagnacijos perkrovimas     | ✅                | ✅            |
| 4. HoF atgalinis įpurškimas    |                   | ✅            |
| 5. Biudžeto suvokimas          | ✅                | ✅            |
| 6. Įvairi inicializacija       | ✅                |               |
| 7. Hibridinis parinkimas       | ✅                | ✅            |
| 8. Daugkartinės mutacijos gylis|                   | ✅            |

Nei viena iš šių savybių nėra `eaSimple` algoritme. Kiekviena iš jų yra
nedidelis, gerai suprantamas patobulinimas; kartu jos sudaro algoritmą,
kurio tikėtinas balas pagal konkurso normalizavimo schemą griežtai
dominuoja atskaitos algoritmą pakartotinių bandymų ribose.

---

## Literatūra

- Rudolph, G. (1994). *Convergence analysis of canonical genetic
  algorithms.* IEEE Trans. Neural Networks 5(1).
- Davis, L. (1989). *Adapting operator probabilities in genetic
  algorithms.* ICGA-89.
- Fialho, Á., Da Costa, L., Schoenauer, M., Sebag, M. (2010).
  *Analyzing bandit-based adaptive operator selection mechanisms.*
  Annals of Mathematics and AI 60.
- Grefenstette, J. J. (1992). *Genetic algorithms for changing
  environments.* PPSN II.
- Eshelman, L. J. (1991). *The CHC adaptive search algorithm.* FOGA-1.
- Goldberg, D. E., Deb, K. (1991). *A comparative analysis of selection
  schemes used in genetic algorithms.* FOGA-1.
- Hansen, N., Ostermeier, A. (2001). *Completely derandomized
  self-adaptation in evolution strategies.* Evol. Comput. 9(2).
