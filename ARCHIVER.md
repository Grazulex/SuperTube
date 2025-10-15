# SuperTube Archiver Service

Service automatique d'archivage des données historiques pour maintenir les performances et gérer la rétention à long terme.

## Vue d'ensemble

Le service archiver s'exécute quotidiennement à **3h du matin** pour:
- Archiver automatiquement les statistiques de plus de 90 jours
- Compresser les données avec zlib (économie ~75-80% d'espace)
- Maintenir les tables actives optimisées
- Logger tous les archivages dans `/app/data/archive.log`

## Architecture

### Hot/Cold Data Strategy
- **Hot data (0-90 jours)**: Tables normales, accès rapide
- **Cold data (90+ jours)**: Tables archive compressées (BLOB)
- **Rétention totale**: 365 jours (1 an)

### Tables
- `stats_history` → `stats_history_archive` (après 90j)
- `video_stats_history` → `video_stats_history_archive` (après 90j)

## Utilisation

### Démarrer le service archiver

```bash
# Démarrer uniquement le service archiver
docker-compose up -d archiver

# Démarrer tous les services (supertube + archiver)
docker-compose up -d
```

### Arrêter le service archiver

```bash
docker-compose stop archiver
```

### Vérifier les logs d'archivage

```bash
# Logs Docker (cron daemon)
docker-compose logs -f archiver

# Logs d'archivage détaillés
cat data/archive.log
tail -f data/archive.log  # Suivre en temps réel
```

### Exécution manuelle

Vous pouvez lancer l'archivage manuellement sans attendre le cron:

```bash
# Exécuter l'archivage maintenant
docker-compose exec archiver python src/archiver_cron.py

# Archiver données de plus de 60 jours
docker-compose exec archiver python src/archiver_cron.py --days 60

# Dry run (simulation sans modifications)
docker-compose exec archiver python src/archiver_cron.py --dry-run
```

## Configuration

### Modifier l'heure d'exécution

Éditez `docker-compose.yml`, ligne du cron:

```yaml
# Actuellement: 0 3 * * * (3h du matin tous les jours)
# Format: minute heure jour mois jour_semaine

# Exemples:
# 0 2 * * *     → 2h du matin tous les jours
# 0 3 * * 0     → 3h du matin tous les dimanches
# 0 */6 * * *   → Toutes les 6 heures
```

Puis redémarrer:
```bash
docker-compose restart archiver
```

### Modifier la période d'archivage

Par défaut 90 jours, modifiable dans `docker-compose.yml`:

```yaml
command: >
  sh -c "
  echo '0 3 * * * cd /app && python src/archiver_cron.py --days 60 >> /app/data/archive.log 2>&1' > /etc/crontabs/root &&
  crond -f -l 2
  "
```

## Opérations de Maintenance

### Export/Backup complet

```python
# Dans un script Python ou shell interactif
from src.database import DatabaseManager
import asyncio

async def backup():
    db = DatabaseManager()
    result = await db.export_database("/app/data/backups/backup-2025-10-15.db")
    print(f"Backup créé: {result['export_path']}")
    print(f"Taille: {result['export_size_bytes']} bytes")

asyncio.run(backup())
```

### Purge manuelle des anciennes archives

Pour libérer de l'espace en supprimant des archives très anciennes:

```python
from src.database import DatabaseManager
import asyncio

async def purge():
    db = DatabaseManager()

    # Supprimer les archives de plus de 2 ans
    result = await db.purge_old_data(purge_archive_days=730)

    print(f"Archives supprimées: {result.get('stats_history_archive', 0)}")
    print(f"Video archives supprimées: {result.get('video_stats_history_archive', 0)}")

asyncio.run(purge())
```

### Vérifier l'état de l'archivage

```bash
# Voir les dernières lignes du log
tail -20 data/archive.log

# Rechercher les erreurs
grep ERROR data/archive.log

# Compter les archivages réussis
grep "completed successfully" data/archive.log | wc -l
```

## Monitoring

### Logs typiques d'un archivage réussi

```
[2025-10-15T03:00:01] Starting archival process (>= 90 days)...
[2025-10-15T03:00:02] Archival completed successfully:
[2025-10-15T03:00:02]   - Channel stats archived: 1250
[2025-10-15T03:00:02]   - Video stats archived: 8300
[2025-10-15T03:00:02]   - Total records archived: 9550
```

### Logs quand rien à archiver

```
[2025-10-15T03:00:01] Starting archival process (>= 90 days)...
[2025-10-15T03:00:01] Archival completed successfully:
[2025-10-15T03:00:01]   - Channel stats archived: 0
[2025-10-15T03:00:01]   - Video stats archived: 0
[2025-10-15T03:00:01]   - Total records archived: 0
[2025-10-15T03:00:01]   - No data to archive (all data is within retention period)
```

### En cas d'erreur

```
[2025-10-15T03:00:01] ERROR during archival: DatabaseError: unable to open database file
[2025-10-15T03:00:01] Traceback:
...
```

Si vous voyez des erreurs:
1. Vérifiez les permissions sur `/app/data/`
2. Vérifiez que le fichier `supertube.db` existe
3. Consultez les logs Docker: `docker-compose logs archiver`

## Désactivation

Si vous ne souhaitez pas utiliser l'archivage automatique:

```bash
# Arrêter et désactiver le service
docker-compose stop archiver

# Ou commenter le service dans docker-compose.yml
# services:
#   archiver:
#     ...
```

Note: L'archivage manuel reste possible via les scripts Python.

## Performance

- **Temps d'exécution**: ~1-5 secondes pour 10,000 enregistrements
- **Impact CPU**: Minimal (s'exécute à 3h du matin)
- **Espace économisé**: ~75-80% via compression zlib
- **Impact sur l'app principale**: Aucun (tables séparées)

## Troubleshooting

### Le service ne démarre pas

```bash
# Vérifier les logs
docker-compose logs archiver

# Reconstruire l'image si nécessaire
docker-compose build archiver
docker-compose up -d archiver
```

### Le cron ne s'exécute pas

```bash
# Vérifier que le cron est actif
docker-compose exec archiver ps aux | grep crond

# Vérifier la configuration cron
docker-compose exec archiver cat /etc/crontabs/root

# Tester l'exécution manuelle
docker-compose exec archiver python src/archiver_cron.py
```

### Permissions denied sur archive.log

```bash
# Créer le fichier avec les bonnes permissions
touch data/archive.log
chmod 666 data/archive.log
```
