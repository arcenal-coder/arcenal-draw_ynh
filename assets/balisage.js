/* Distances réelles des points visibles, jamais recalculées à partir du dernier point. */
globalThis.CrobardBalisage = Object.freeze({
  entries(zones, fallback) {
    const distinct = new Map();
    for (const zone of zones.length ? zones : [fallback]) {
      const distance = Number(zone.distance ?? zone.radius);
      const threshold = zone.threshold === 'manual' ? 'manual' : Number(zone.threshold) === 25 ? 25 : 2.5;
      const attenuated = zone.attenuated !== false;
      if (!Number.isFinite(distance) || distance < 0) continue;
      const key = `${threshold}:${distance}:${attenuated}`;
      if (!distinct.has(key)) distinct.set(key, { threshold, distance, attenuated });
    }
    const order = (value) => value === 'manual' ? 2 : value === 25 ? 1 : 0;
    return [...distinct.values()].sort((a, b) => order(a.threshold) - order(b.threshold) || a.distance - b.distance || Number(b.attenuated) - Number(a.attenuated));
  },
  label(threshold) {
    return threshold === 'manual' ? 'Balisage manuel' : threshold === 25 ? 'Balisage 25 µSv/1h' : 'Balisage 2,5 µSv/h';
  },
});
