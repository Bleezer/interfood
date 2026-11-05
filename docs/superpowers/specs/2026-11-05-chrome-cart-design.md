# Chrome kosársegéd

## Elfogadott cél
A felhasználó számítógépen, Chrome-ban használja az Interfoodot. Bejelentkezés
után a következő hétre napi egy fő ajánlat és legfeljebb két alternatíva
mindegyikéből egy adag kerüljön a kosárba. A nem kívánt ételeket ő veszi ki.
Rendelést/fizetést csak a felhasználó véglegesít.

## Megoldás
Chrome Manifest V3-bővítmény és Windows native messaging Python-host.
A bővítmény csak az Interfood étlapját figyeli és az oldal saját pluszgombjait
használja. A helyi Python-host kizárólag a nyilvános étlapséma normalizálását
és a meglévő recommendation/ szabályait futtatja; nem módosít kosarat.
Az oldal /api/v1/menu válaszát és a /api/v1/user sikeréből csak a számszerű
fiókazonosítót figyeljük. Jelszót, tokent, címet és request headert nem olvasunk.
A teljes user-választ nem továbbítjuk a bővítménybe.

Alternatívák: helyi HTTP-szerver állandó futó folyamatot igényelne; a felhős
ajánlat nyilvános publikálása vagy GitHub-token a bővítményben kerülendő többlet.
A natív kapcsolat a már meglévő Python-kódot használja, új szolgáltatás nélkül.

## Heti adatok
A következő hét a Europe/Budapest szerinti hétfő. A bővítmény a megfelelő
hetet választja az oldalon, és az éppen betöltött étlapból frissen számít
ajánlást. Ez azonos adatok mellett a Telegraméval azonos, későbbi forrásváltozás
esetén eltérhet a korábban elküldött riporttól. Nem kell GitHub- vagy
Telegram-hitelesítés a Chrome-ba.

## Duplázás és hibák
A helyi Chrome-tároló fiók/heti dátum/ételazonosító szerint rögzíti a tételeket.
A már kosárban lévő tételből nem ad további adagot. A sikeresen egyszer
feltöltött, majd kézzel kivett ételt a következő belépés sem teszi vissza.
Kattintás előtt tartós pending jelzés; bizonytalan eredménynél nincs újabb
kattintás. Több lap között a háttérfolyamat sorosítja a foglalásokat.
Hibánál állapotjelzés és leállás; nincs automatikus helyettesítés.
A meglévő kosár más tételei érintetlenek maradnak.
Ki/be kapcsoló a bővítmény felugró ablakában. Nincs kosártörlés vagy checkout.

## Telepítés és ellenőrzés
Unpacked bővítmény telepítése chrome://extensions alatt, egyszeri helyi host
regisztrációval HKCU-ban. Stabil, nem titkos manifest key rögzíti az azonosítót.
A natív host csak ezt az extension origint fogadja. A .local/ hostmanifest és
launcher nem kerül Gitbe. Nincs új Python- vagy npm-függőség.
Offline Python- és Node-tesztek, izolált DOM-próba; valódi kosárteszt csak a
telepített Chrome-ban. A jelenlegi számítógép-vezérlés Node runtime hibája
miatt a felhasználói Chrome közvetlen vizsgálata most nem elérhető.
