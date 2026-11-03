# Külön futtatható ebédválogató

A jóváhagyott irány: az interfood/ gyűjt és egységesít, a recommendation/
kizárólag a mentett JSON-ból ajánl, hálózat és Playwright nélkül.
A kapcsolat data/menu.json; nyers forrás data/raw.json. A JSON-séma nem változik.
Az egyes fájlok cseréje atomikus; üres/hibás gyűjtés egyik fájlt sem írja át.
A korábbi dátumos helyi fájlokat nem töröljük automatikusan.

Alternatívák: a gyűjtőbe épített ajánló összekeverné a felelősségeket;
külön szolgáltatás szükségtelen. A külön Python-csomagot választottuk.

Napi egy ebéd csak a kínált hétfő–szombati napokra. Legalább 40 g fehérje,
30 g alatti zsír, fehérje >= 2 * zsír; előny a >= 3 * zsír.
Sorok: Fitnessz, Karcsúsító, Sport, majd más főételek.
Szombaton a rántott hús előnyt kap, a számszerű korlátok puhák;
minden eltérést kiírunk. Hiányzó tápértékkel nem ajánlunk.
Hal, tengeri étel és gyümölcsös hús kizárva. Ár és kalória nem rangsorol.

Első változat: átlátható szöveges felismerés név és összetevők alapján,
nem AI-agent. Nem teljes körű szemantikai osztályozás; bizonytalan ételnél
a felhasználó ellenőrizheti a kiválasztást. A profil külön JSON-ban, Gitben
tárolható; a futási étlap és ajánlás nem. Nem adunk orvosi minősítést.
