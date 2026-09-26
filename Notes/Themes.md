# Bible Themes

Browse verses by theme. Queries read `tags` and show each page's `aliases`.
Enable the **Dataview** community plugin for these tables to render
(`Settings → Community plugins → Dataview`).

## Trust

```dataview
TABLE aliases AS "Alias"
FROM "Bible"
WHERE contains(tags, "trust")
SORT file.name ASC
```

## Strength & Power

```dataview
TABLE aliases AS "Alias"
FROM "Bible"
WHERE contains(tags, "strength") OR contains(tags, "power")
SORT file.name ASC
```

## Not by Human Might (horses, chariots, armies, war)

```dataview
TABLE aliases AS "Alias"
FROM "Bible"
WHERE contains(tags, "horses") OR contains(tags, "chariots") OR contains(tags, "army") OR contains(tags, "war")
SORT file.name ASC
```

## Grace & Weakness

```dataview
TABLE aliases AS "Alias"
FROM "Bible"
WHERE contains(tags, "grace") OR contains(tags, "weakness") OR contains(tags, "weak")
SORT file.name ASC
```

## Spirit

```dataview
TABLE aliases AS "Alias"
FROM "Bible"
WHERE contains(tags, "spirit")
SORT file.name ASC
```

## All verses

```dataview
TABLE aliases AS "Alias", tags AS "Tags"
FROM "Bible"
SORT file.name ASC
```
