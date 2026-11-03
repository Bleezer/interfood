# Felhős heti ajánló és Telegram

A gépednek nem kell bekapcsolva lennie: a GitHub Actions gyűjt, majd a
meglévő szabályalapú ajánlót futtatja. AI-agentet ez a bekötés nem ad hozzá.
Az étlapadat csak az adott futás munkakönyvtárában él, nem készül archívum.

## 1. Repository

A projekt tárhelye: https://github.com/Bleezer/interfood
A workflow a repository alapértelmezett ágán legyen.
A személyes profil miatt a privát láthatóság célszerű; a futtatás a GitHub
Actions-fiókkeretet használja. Nincs automatikus csomagvásárlás.

## 2. Telegram-bot

1. Telegramon nyisd meg a hivatalos [BotFather](https://t.me/BotFather) beszélgetést.
2. Írd be: `/newbot`, és válassz botnevet, illetve felhasználónevet.
3. A kapott tokent tedd félre a GitHub Secret beállításához; ne írd a kódba vagy ide a chatbe.
4. Nyisd meg a saját új botodat, és küldj neki `/start` üzenetet.
5. PowerShellben, a projekt mappájában futtasd:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m delivery.setup
```

A token bevitele rejtett; nem mentjük. A parancs csak a saját botod privát
beszélgetéseinek számszerű azonosítóit írja ki, üzenetet nem küld.
Friss /start szükséges, ha nincs eredmény; a Telegram az új frissítéseket
legfeljebb 24 óráig tartja meg. Több azonosítónál a saját beszélgetésedet válaszd.

## 3. GitHub Secrets

A repositoryban: Settings → Secrets and variables → Actions → New repository secret.

- `TELEGRAM_BOT_TOKEN`: a BotFather által adott token.
- `TELEGRAM_CHAT_ID`: a beállítóparancs által kiírt számszerű azonosító.

A titkok csak a konfigurációellenőrzés és küldés lépéseiben érhetők el.
A bot tokenjét a kód és az alkalmazás hibaszövege nem írja ki.

## 4. Első telefonos próba

GitHub → Actions → Weekly Interfood recommendations → Run workflow.
Jelöld be a `test_notification` mezőt. Ez nem gyűjt étlapot, csak rövid
tesztüzenetet küld. A telefonon a Telegram és a bot értesítései legyenek
bekapcsolva.

Utána újra Run workflow, a tesztjelölő nélkül: ez már friss gyűjtést és a
teljes heti ajánlót küldi. A hosszabb riport több üzenetben érkezik.
Ha hiba történik, a job piros lesz, és lehetőség szerint rövid hibajelzést küld.
Részleges kézbesítés után a kézi újrafuttatás korábban megkapott részeket is
újraküldhet; bizonytalan hálózati hibát automatikusan nem próbálunk újra.

## 5. Ütemezés

Előkészített alapérték: péntek 10:00, `Europe/Budapest`, téli-nyári időszámítással.
A felhasználó más időpontot is választhat. Átállítás:
`.github/workflows/weekly-menu.yml` → `on.schedule`.
A cron nem percre pontos szolgáltatás; GitHub-terhelésnél késhet.

Ha a következő hét még nem elérhető, az üres/hibás étlap nem kerül kiküldésre.
Ilyenkor a hiba okát az Actions naplója mutatja; később kézzel újraindítható.
Régi hetet nem tüntetünk fel új ajánlóként.

Helyi offline előnézet (nincs értesítés és nem kér titkot):

```powershell
.\.venv\Scripts\python.exe -X utf8 -m delivery --dry-run
```

## Források

- [GitHub Actions ütemezés](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram-bot létrehozás](https://core.telegram.org/bots/tutorial)
