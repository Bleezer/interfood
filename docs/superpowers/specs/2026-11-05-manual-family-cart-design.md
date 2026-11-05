# Kézi, családtagonkénti kosárfeltöltés

A felhasználó módosítása: belépéskor semmi ne kerüljön a kosárba.
A sarokban személyválasztó és Kosárba teszem gomb jelenjen meg.
Közös Interfood-fiókot használ három családtag: a felhasználó, felesége és fia.
Csak a felhasználó preferenciái ismertek; a másik kettő nem kaphat másolt szabályokat.

Megoldás: helyi profillista, meglévő saját profil, két inaktív helykitöltő.
A listában csak konfigurált profil indítható. A natív terv explicit profile_id-t
kér és ad vissza. Az ismeretlen/hiányzó profil hibát ad, nincs csendes fallback.
A CLI külön --person argumentummal is használhatja a listát.

A kézi művelet fiók/hét/személy szerint egyszer indulhat. Tartós running
állapot a kattintások előtt; done vagy bizonytalan után ismét nem indul.
Ismételt gombnyomáskor rövid 'erre a hétre már megtörtént' állapotjelzés.
A korábbi automatikus feltöltés adatai a saját profilnak számítanak; az
átállás nem törli a korábbi védelmet.

Közös étel esetén a második személynek egy új adag kerül be. Az első
személy még elfogadja a kézzel már betett adagot (régi működés).
Ha korábbi személy adagját közben kivették, nem állítjuk vissza;
az új személynek pontosan egy új adag kerül be.
Tételenként nyilvántartott személyekkel különböztetjük meg ezeket az eseteket.

Fiókváltás, megszakítás, több fül, régi hét és bizonytalan kattintás továbbra
is leállítja vagy tiltja az újabb feltöltést. Nem változik a gyűjtő,
a tápértékszabály, az étlapséma, az értesítési címzett és a rendelési korlát.
