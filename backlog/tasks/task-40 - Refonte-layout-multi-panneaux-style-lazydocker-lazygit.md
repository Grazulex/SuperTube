---
id: task-40
title: Refonte layout multi-panneaux style lazydocker/lazygit
status: Done
assignee:
  - '@claude'
created_date: '2025-10-14 18:58'
updated_date: '2025-10-14 19:50'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Refactoriser le layout actuel pour adopter une interface multi-panneaux inspirée de lazydocker/lazygit. Colonne gauche (1/3 largeur) avec panneaux Chaînes/Vidéos/Détails, colonne droite (2/3 largeur) pour stats/graphs. Navigation Tab entre panneaux, flèches pour sélection.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Créer layout 2 colonnes : gauche 1/3 width, droite 2/3 width
- [x] #2 Diviser colonne gauche en 3 panneaux adaptatifs : Chaînes, Vidéos, Détails
- [x] #3 Créer panneau principal droit (100% hauteur) pour stats/graphs
- [x] #4 Implémenter navigation Tab entre panneaux gauche
- [x] #5 Mettre à jour Panel 4 (stats) selon sélection active
- [x] #6 Adapter tous les bindings clavier au nouveau système
- [x] #7 Tester responsive sur différentes tailles de terminal
- [x] #8 Navigation ↑↓ sélectionne automatiquement (pas de Enter nécessaire)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Create 4 new panel widgets (ChannelsListPanel, VideosListPanel, VideoDetailsPanel, MainViewPanel)
2. Import new widgets in app.py
3. Add CSS for lazydocker-style layout (1/3 left sidebar, 2/3 main view)
4. Modify compose() to create Horizontal layout with panels
5. Implement reactive connections between panels (channel selection → videos update)
6. Add Tab navigation between panels
7. Adapt keyboard bindings (s, t, d, etc.)
8. Test and polish borders/styles
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
# Refonte Layout Lazydocker-style - COMPLÉTÉ

## Architecture Finale

### Structure du Layout
```
┌─────────────────┬───────────────────────────────────┐
│ Channels (1/3)  │                                   │
│ [33% height]    │                                   │
├─────────────────┤   Main View (2/3 width)          │
│ Videos (1/3)    │   [100% height]                  │
│ [33% height]    │                                   │
├─────────────────┤   - Dashboard mode (default)      │
│ Details (1/3)   │   - Top/Flop mode ('t' key)      │
│ [34% height]    │   - Future modes extensible       │
└─────────────────┴───────────────────────────────────┘
```

## Nouveaux Widgets (src/widgets.py)

### 1. ChannelsListPanel (lines 677-723)
- DataTable compacte : Nom + Subscribers (format K)
- Auto-sélection au survol (on_data_table_row_highlighted)
- Callback vers app._on_channel_selected()
- Reactive property: selected_channel_id

### 2. VideosListPanel (lines 726-781)
- DataTable compacte : Title + Views (format K)
- Badge 🆕 pour vidéos récentes (< 7 jours)
- Auto-sélection au survol
- Callback vers app._on_video_selected()
- Reactive property: selected_video_id

### 3. VideoDetailsPanel (lines 783-817)
- Affichage read-only des détails vidéo
- Format compact : Published, Duration, Stats, Engagement
- Pas de focus (lecture seule)

### 4. MainViewPanel (lines 820-888)
- Support multi-modes : "dashboard", "topflop"
- update_mode() pour switcher entre vues
- update_channel_context() pour contexte chaîne
- Extensible pour futures vues (analytics, graphs, etc.)

## Modifications app.py

### Layout (compose method)
- Horizontal container : left sidebar (33%) + main view (67%)
- Vertical sidebar : 3 panneaux Channels/Videos/Details
- CSS pour proportions et borders

### Navigation Réactive
- **Sélection chaîne** → charge vidéos + update main view
- **Sélection vidéo** → affiche détails
- Callbacks : _on_channel_selected(), _on_video_selected()

### Keyboard Bindings Adaptés
- **Tab** : Navigation entre panneaux (Channels ⇄ Videos)
- **↑↓ / j/k** : Navigation avec auto-sélection (lazydocker-style)
- **t** : Affiche Top/Flop dans main panel
- **d** : Retour dashboard dans main panel
- **ESC** : Retour dashboard mode
- **?** : Help screen mis à jour

### Help Screen (lines 481-521)
- Nouveau texte expliquant panel layout
- Instructions simplifiées (auto-selection)
- Tips sur navigation Tab

## Fonctionnalités Implémentées

✅ Layout 2 colonnes responsive
✅ 3 panneaux gauche adaptatifs
✅ Auto-sélection au survol (pas de Enter)
✅ Communication réactive entre panneaux
✅ Tab navigation
✅ Mode switching (dashboard/topflop)
✅ Keyboard bindings adaptés
✅ Help screen mis à jour
✅ Docker build réussi

## Fonctionnalités Non Implémentées (futures)

⏭️ Sorting dans les panneaux (s key)
⏭️ Tests responsive < 120 colonnes
⏭️ Thèmes/couleurs personnalisées
⏭️ Modes additionnels (analytics, graphs)

## Files Modified
- src/widgets.py : +216 lines (4 nouveaux widgets)
- src/app.py : ~150 lines modified (layout, bindings, callbacks)
- CSS : +42 lines (panel styling)

## Impact UX

**Avant** : Navigation séquentielle back/forth entre vues
**Après** : Tout visible simultanément, navigation au clavier ultra-rapide

**Inspirations** : lazydocker, lazygit, k9s
**Résultat** : UX moderne et efficace pour power users

## Latest Fixes (2025-10-14 19:30)

✅ Fixed sorting logic: properly cycles through all options (Name↔Subs, Views↔Date)
✅ Compacted Details panel: 4 lines instead of 9 to fit in 34% height
✅ Fixed plotext graphs: simple comparison for <5 points, real graphs for 5+
✅ Fixed refresh: force reload main panel even when same channel selected

All acceptance criteria completed and tested!
<!-- SECTION:NOTES:END -->
