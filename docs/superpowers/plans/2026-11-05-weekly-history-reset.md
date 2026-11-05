# Heti feltöltési előzmények törlése

A felhasználó kérése: egyetlen opció felejtse el a hét korábbi
kosárfeltöltését mindhárom személyre. Ez nem rendelésellenőrzés.

- [x] Törlés kizárólag a bejelentkezett fiók következő hetére, minden profilra.
- [x] Legacy ledger, perprofil tétel- és futásállapot, terv és közös hozzájárulók törlése.
- [x] Más fiókok/hetek, személyes szabályok és kosár megőrzése.
- [x] Aktív futásnál tiltás; stale futás törölhető.
- [x] Reset-epoch akadályozza, hogy régi üzenet új futásba avatkozzon.
- [x] Sarokpanel törlőgomb, célhetet mutató megerősítés, stabil visszajelzés.
- [x] Node RED → GREEN: teljes scope, aktív/stale, régi állapotok, elavult üzenetek.
- [x] DOM RED → GREEN: visszavonás, változatlan kosár, új kézi feltöltés.
- [x] Külön read-only kódreview: nincs blokkoló észrevétel.
- [x] Teljes unittest, Node-tesztek, DOM-próba és compileall.
- [x] Commit és push; Chrome környilas frissítése a felhasználónál.

A valódi kosárhoz a fejlesztői ellenőrzések nem nyúltak.
