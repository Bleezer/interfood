# Chrome kosársegéd telepítése

Ez a rész a felhasználó külön kérésére módosíthatja a kosarat:
a következő hét napi fő ajánlatát és két különböző alternatíváját egy-egy
adaggal beteszi. Nem véglegesít rendelést és nem fizet.
A felhős heti Telegram-küldés továbbra is önállóan működik.

## Egyszeri telepítés

1. A projekt gyökeréből futtasd:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m cart_assistant.install
```

Ez a saját Windows-felhasználód Chrome NativeMessagingHosts bejegyzését állítja
be. Nem kell rendszergazdai jog. A helyi launcher a projekt .venv Pythonját
használja, a .local/ mappába kerül, és nem kerül Gitbe.

2. Chrome-ban nyisd meg: `chrome://extensions`.
3. Jobb felül kapcsold be a **Fejlesztői módot**.
4. Válaszd a **Kicsomagolt bővítmény betöltése** lehetőséget.
5. Válaszd ki ezt a mappát: `C:\private\interfood\extension`.

Ha a bővítményt a telepítő előtt töltötted be, az Interfood-lapot frissítsd.
A bővítménynek a projekt mappájában kell maradnia. A manifest key rögzíti
az azonosítóját, ezért frissítés után is ugyanahhoz a hosthoz kapcsolódik.

## Első bejelentkezett próba

Nyisd meg a https://rendel.interfood.hu/ étlapot, és jelentkezz be.
A bővítmény kiválasztja a következő hetet, majd a kínált napokon végiglép.
A jobb alsó sarokban látszik, hány tétel került a kosárba, és miért állt le,
ha valamelyik étel közben már nem rendelhető.

A kosárban minden ajánlatból legfeljebb egy új adag lesz.
A már bent lévő tétel mennyiségét nem növeli, más tételeket nem töröl.
A feltöltés után vedd ki, ami nem kell, majd te véglegesítsd a rendelést.

A bővítmény az éppen betöltött étlapból, a helyi recommendation/profile.json
szabályaival számol újra. Azonos adatok mellett ez megegyezik a Telegram
ajánlataival. Későbbi menü- vagy profilváltozás eltérő jelölteket adhat.

## Duplázás és megszakítás

Fiók, hét és ételazonosító szerint megjegyzi, mit kezelt már.
A kézzel kivett ételt nem teszi vissza oldalfrissítéskor vagy új belépéskor.
Bizonytalan kattintási eredménynél megáll, és a tételt automatikusan nem próbálja újra.
Ezt a tételt kézzel ellenőrizd; a többi tételt is kézzel befejezheted.

A másik Interfood-fülön történt belépés/kilépés vagy fiókváltás megszakítja a
korábbi fül automatizmusát; ilyenkor frissítsd a használni kívánt lapot.
Több fül ugyanazt a tételt nem foglalhatja le egyszerre.

A bővítmény ikonjánál az **Automatikus kosárfeltöltés** kapcsolóval bármikor
kikapcsolhatod. A már betett ételeket a kikapcsolás nem veszi ki.

A bővítmény eltávolítása vagy helyi adatainak törlése a korábbi feltöltési
emlékezetet is törli. Ilyenkor a még kosárban lévő tételeket kihagyja,
de a korábban kézzel kivett ételekre már nem emlékszik.

## Fejlesztői ellenőrzés

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest -v
node --test extension/tests/*.test.cjs
.\.venv\Scripts\python.exe -X utf8 scripts/check_cart_dom.py
```

Az utolsó parancs minden URL-t helyi HTML-re cserél; nem küld valódi kosárkérést.
Az első valódi kosárfeltöltést a telepített Chrome-bővítménnyel kell ellenőrizni.

## Eltávolítás

Chrome → Bővítmények → Interfood kosársegéd → Eltávolítás.
A helyi host külön eltávolítása PowerShellből:

```powershell
Remove-Item -LiteralPath 'HKCU:\Software\Google\Chrome\NativeMessagingHosts\hu.interfood.menu_helper'
```

Ez csak a host regisztrációját törli, a projektet és étlapadatokat nem.
