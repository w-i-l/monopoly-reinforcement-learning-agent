const areGameStateEqual = (state1, state2) => {
  if (!state1 || !state2) return false;

  if (state1.currentPlayer !== state2.currentPlayer) return false;

  if (state1.ownedProperties.length !== state2.ownedProperties.length)
    return false;
  if (
    !state1.ownedProperties.every(
      (prop, i) => prop === state2.ownedProperties[i]
    )
  )
    return false;

  if (state1.mortgagedProperties.length !== state2.mortgagedProperties.length)
    return false;
  if (
    !state1.mortgagedProperties.every(
      (prop, i) => prop === state2.mortgagedProperties[i]
    )
  )
    return false;

  if (state1.players.length !== state2.players.length) return false;

  for (let i = 0; i < state1.players.length; i++) {
    const p1 = state1.players[i];
    const p2 = state2.players[i];

    if (p1.name !== p2.name) return false;
    if (p1.balance !== p2.balance) return false;
    if (p1.position !== p2.position) return false;
    if (p1.in_jail !== p2.in_jail) return false;
    if (p1.escape_jail_cards !== p2.escape_jail_cards) return false;

    if (JSON.stringify(p1.houses) !== JSON.stringify(p2.houses)) return false;
    if (JSON.stringify(p1.hotels) !== JSON.stringify(p2.hotels)) return false;

    if (p1.properties.length !== p2.properties.length) return false;
    if (!p1.properties.every((prop, j) => prop.id === p2.properties[j].id))
      return false;
  }

  return true;
};

export default areGameStateEqual;
