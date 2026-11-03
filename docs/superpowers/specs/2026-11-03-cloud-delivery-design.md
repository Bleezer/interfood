# Felhős futtatás és telefonos értesítés

A felhasználó heti ütemezést és kikapcsolt számítógép mellett működő
telefonos értesítést kér; a csatornát ránk bízta.

Választott megoldás: GitHub Actions + Telegram Bot API.
Alternatíva a helyi ütemezés, de az bekapcsolt gépet igényel.
Saját szerver vagy OpenAI API ebben a lépésben nem szükséges.
A meglévő szabályalapú ajánlót futtatjuk; AI-agent nincs hozzáadva.

A workflow előbb offline teszteket, majd nyilvános étlapgyűjtést futtat,
végül a napi fő ajánlatot és két alternatívát Telegramra küldi.
A gyűjtés és ajánlás külön csomag marad, a delivery/ csak kézbesít.
A szövegformázás közös a CLI és az értesítés számára.
Hiányzó vagy nem a következő hétre szóló étlapot nem küldünk ki.
A hibáról külön rövid értesítés indulhat. Nincs rendelés vagy kosármódosítás.

A válaszra váró ütemezés alapértéke: péntek 10:00 Europe/Budapest.
Kézi workflow_dispatch is lesz. Fiókok, távoli repo és Telegram-célpont
nélkül a felhős aktiválás blokkolt; a helyi előkészítés elvégezhető.
TELEGRAM_BOT_TOKEN és TELEGRAM_CHAT_ID GitHub Actions Secrets-be kerül,
kódba vagy naplóba nem. A botnak a címzett előbb írjon /start üzenetet.
A számozott tápértékhatárok, szünnapkezelés és JSON-séma nem változik.

A küldés időkorlátos, hosszú szöveget a Telegram korlátja alá darabol.
Bizonytalan hálózati hiba után nincs automatikus újraküldés, mert duplázhat.
A felhő minden futáskor frissen gyűjt; nem tárolunk heti archívumot.
Nem ígérünk percre pontos cron-futást vagy működő telefontesztet aktiválás előtt.
