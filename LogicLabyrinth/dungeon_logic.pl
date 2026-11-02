% ==========================================
% LOGIC LABYRINTH - PROLOG DUNGEON CORE
% ==========================================

% --- 1. ITEM KNOWLEDGE BASE ---
% Format: item(ID, Name, Type, BuffStat, BuffVal, DebuffStat, DebuffVal, Description)

% Weapons
item(w1,  rusted_dagger,      weapon, attack, 3,  none,    0, 'A dull blade. Better than bare fists.').
item(w2,  iron_sword,         weapon, attack, 5,  none,    0, 'A reliable standard-issue blade.').
item(w3,  silver_rapier,      weapon, attack, 6,  defense, 2, 'Fast but leaves your guard open.').
item(w4,  heavy_battleaxe,    weapon, attack, 8,  defense, 4, 'Massive power, slow and risky.').
item(w5,  mystic_staff,       weapon, attack, 7,  none,    0, 'Channels arcane energy through your strikes.').
item(w6,  obsidian_blade,     weapon, attack, 6,  defense, 3, 'Razor sharp, but brittle on defense.').
item(w7,  glowing_broadsword, weapon, attack, 7,  none,    0, 'Radiates a holy light against darkness.').
item(w8,  shadow_dagger,      weapon, attack, 5,  none,    0, 'Quick strikes from the shadows.').
item(w9,  dragon_lance,       weapon, attack, 9,  defense, 5, 'Legendary reach, but leaves flanks exposed.').
item(w10, cursed_blade,       weapon, attack, 12, hp,      10, 'Raw power, but it bites back.').

% Armor
item(a1,  leather_tunic,      armor, defense, 3,  none,    0, 'Basic flexible protection.').
item(a2,  chainmail,          armor, defense, 5,  none,    0, 'Sturdy interlocked metal links.').
item(a3,  steel_breastplate,  armor, defense, 6,  attack,  2, 'Solid but restricts your swing.').
item(a4,  elven_cloak,        armor, defense, 4,  none,    0, 'Silent, light, magic-woven cloth.').
item(a5,  dragon_scale_mail,  armor, defense, 8,  attack,  3, 'Near impenetrable, but very heavy.').
item(a6,  knight_greaves,     armor, defense, 5,  attack,  2, 'Heavy plate for your legs, slows strikes.').
item(a7,  magic_robe,         armor, defense, 5,  none,    0, 'Woven with protective runes.').
item(a8,  titan_plate,        armor, defense, 9,  attack,  5, 'Forged in volcanic depths. Barely movable.').
item(a9,  shadow_mail,        armor, defense, 4,  none,    0, 'Absorbs incoming physical blows silently.').
item(a10, cursed_shield,      armor, defense, 11, attack,  6, 'Absorbs everything — including your will.').

% Consumables
item(c1,  minor_health_potion, consumable, hp,      20, none,    0, 'Restores a small amount of health.').
item(c2,  major_health_potion, consumable, hp,      45, none,    0, 'Heals deep wounds instantly.').
item(c3,  stamina_elixir,      consumable, attack,   5, none,    0, 'Temporarily sharpens your strikes.').
item(c4,  mana_crystal,        consumable, defense,  5, none,    0, 'Awakens a brief defensive barrier.').
item(c5,  golden_nectar,       consumable, hp,      70, none,    0, 'Legendary nectar with strong restorative power.').
item(c6,  elixir_of_vigor,     consumable, hp,      35, none,    0, 'Revitalizing herbal mixture.').
item(c7,  sweet_honey,         consumable, hp,      12, none,    0, 'Simple natural sweetness that heals a little.').
item(c8,  royal_tonic,         consumable, hp,      40, none,    0, 'Brewed for royal champions.').
item(c9,  fire_brew,           consumable, attack,   6, defense, 3, 'Burns through you — power at a cost.').
item(c10, iron_skin_potion,    consumable, defense,  6, attack,  2, 'Skin like steel, but stiff muscles.').

% Trinkets
item(t1,  lucky_coin,      trinket, attack,  3, none,    0, 'A subtle wave of offensive fortune.').
item(t2,  compass_of_truth,trinket, defense, 3, none,    0, 'Guides your footing against attacks.').
item(t3,  ring_of_shadows, trinket, attack,  5, defense, 2, 'Striking from the dark leaves you exposed.').
item(t4,  crystal_prism,   trinket, defense, 4, none,    0, 'Refracts incoming harm away.').
item(t5,  ruby_pendant,    trinket, attack,  4, none,    0, 'Warm to the touch, inspiring courage.').
item(t6,  star_charm,      trinket, defense, 5, attack,  2, 'Celestial warding, but dulls aggression.').
item(t7,  berserker_eye,   trinket, attack,  7, defense, 4, 'Wild bloodlust — you hit hard but feel less.').
item(t8,  guardian_crest,  trinket, defense, 6, attack,  3, 'Emblem of unwavering defense, passive stance.').
item(t9,  phoenix_feather, trinket, hp,     15, none,    0, 'Radiates restorative heat over time.').
item(t10, ancient_tome,    trinket, attack,  4, none,    0, 'Teaches forgotten combat techniques.').

% --- 2. RARE ITEMS ---
% Format: rare_item(ID, Name, Type, BuffStat, BuffVal, DebuffStat, DebuffVal, Description, PassiveName, PassiveDesc)

% Pure blessings
rare_item(r1,  heart_of_the_labyrinth, relic,  hp,      60, none,    0,
    'The dungeon itself pulses through you.',
    vitality_surge,
    'Restores 8 HP at the start of each battle turn.').

rare_item(r2,  godslayer_edge,         relic,  attack,  25, none,    0,
    'A blade said to have wounded a deity.',
    divine_cleave,
    'Every attack has a 25% chance to deal double damage.').

rare_item(r3,  aegis_of_eternity,      relic,  defense, 22, none,    0,
    'Forged beyond the mortal realm.',
    eternal_ward,
    'Reduces all incoming damage by 3, after DEF is applied.').

% High risk / high reward
rare_item(r4,  bloodpact_seal,         relic,  attack,  30, hp,      40,
    'Power sealed in your own blood.',
    blood_price,
    'Deals +8 bonus damage but costs you 3 HP each attack.').

rare_item(r5,  void_gauntlet,          relic,  attack,  20, defense, 15,
    'Crushes everything — including your guard.',
    armor_shred,
    'Each hit permanently lowers the enemy DEF by 1.').

rare_item(r6,  cursed_crown,           relic,  attack,  18, hp,      30,
    'Authority at a terrible price.',
    tyrant_aura,
    'Enemy ATK is reduced by 3 at battle start, but you lose 5 HP.').

rare_item(r7,  shattered_mirror,       relic,  defense, 20, attack,  14,
    'Reflects damage but dulls your edge.',
    mirror_thorns,
    'Reflects 30% of damage taken back to the enemy.').

rare_item(r8,  soulstone_pendant,      relic,  hp,      50, defense, 18,
    'Revives the spirit while weakening the body.',
    second_wind,
    'Once per battle, if HP drops to 0 revive with 20 HP instead.').

% Pure curses
rare_item(r9,  wretched_idol,          relic,  hp,      0,  attack,  20,
    'A hideous relic that saps your strength.',
    sapping_curse,
    'You deal 5 less damage on every attack.').

rare_item(r10, anchor_of_despair,      relic,  hp,      0,  defense, 20,
    'Weighs down your will to resist.',
    leaden_weight,
    'Enemy deals +4 bonus damage on every hit.').

% --- 3. ROOM TYPES ---
room_type(r_entrance,   'Entrance Hall',    combat).
room_type(r_armory,     'Old Armory',       loot).
room_type(r_library,    'Dusty Library',    shrine).
room_type(r_dungeon,    'Prison Block',     combat).
room_type(r_treasury,   'Treasury',         loot).
room_type(r_sanctuary,  'Sanctuary',        rest).
room_type(r_crypt,      'Crypt',            combat).
room_type(r_laboratory, 'Laboratory',       shrine).
room_type(r_barracks,   'Old Barracks',     combat).
room_type(r_garden,     'Corrupted Garden', loot).
room_type(r_dojo,       'Training Dojo',    skill).
room_type(r_oracle,     'Oracle Chamber',   skill).

% --- 4. PLAYER SKILLS ---
% Format: player_skill(ID, Name, Keyword, Description)
% Keyword is what Python checks in player["passives"].
player_skill(sk1,  'Iron Will',        iron_will,      'Reduces all incoming damage by 2.').
player_skill(sk2,  'Quick Strike',     quick_strike,   '20% chance to attack twice per turn.').
player_skill(sk3,  'Battle Trance',    battle_trance,  'Gain +1 ATK permanently after each kill.').
player_skill(sk4,  'Resilience',       resilience,     'Heal 5 HP at the end of every battle turn.').
player_skill(sk5,  'Counter Stance',   counter_stance, 'Reflect 2 damage to the enemy every hit you take.').
player_skill(sk6,  'Predator',         predator,       '+4 bonus damage when enemy HP is below 40%.').
player_skill(sk7,  'Adrenaline',       adrenaline,     '+3 ATK when your own HP drops below 40%.').
player_skill(sk8,  'Shield Crush',     shield_crush,   'Your attacks reduce enemy DEF by 1 (min 0).').
player_skill(sk9,  'Last Stand',       last_stand,     'At 20 HP or below, deal +5 bonus damage.').
player_skill(sk10, 'Fortify',          fortify,        'Gain +1 DEF permanently after each battle.').
player_skill(sk11, 'Bloodlust',        bloodlust,      'Heal 4 HP on every hit you land.').
player_skill(sk12, 'Endurance',        endurance,      'Max HP increased by 20 (applied immediately).').
player_skill(sk13, 'Arcane Insight',   arcane_insight, '15% chance each turn to skip enemy ATK entirely.').
player_skill(sk14, 'War Veteran',      war_veteran,    'Start every battle with +3 temporary ATK.').
player_skill(sk15, 'Undying',          undying,        'Once per floor survive a lethal hit with 1 HP.').

% --- 4. ENEMY KNOWLEDGE BASE ---
room_enemy(goblin_scout,       30, 10,  4).
room_enemy(skeleton_warrior,   45, 14,  7).
room_enemy(dark_cultist,       40, 16,  5).
room_enemy(cave_bat_swarm,     25,  8,  2).
room_enemy(stone_golem_minion, 60, 12, 13).

% --- 5. BOSS KNOWLEDGE BASE ---
% Format: boss(ID, Name, HP, ATK, DEF, Desc, PassiveName, PassiveDesc)
% Floors 1-4: random pool of 8 bosses.  Floor 5: fixed final boss.

% Randomisable bosses (pool for floors 1-4)
boss_pool(b1, goblin_warlord,   100,  20,  10,
    'A ferocious goblin chief wielding a spiked club.',
    war_cry,
    'At battle start raises own ATK by 4. Every 3 turns raises it by 2 more.').

boss_pool(b2, skeleton_knight,  130,  24,  16,
    'An undead warrior clad in rusted plate armor.',
    bone_armor,
    'First 20 damage each battle is completely negated.').

boss_pool(b3, cave_troll,       170,  28,  18,
    'A massive brute with regenerative stone skin.',
    regeneration,
    'Heals 6 HP at the end of every enemy turn.').

boss_pool(b4, shadow_stalker,   150,  34,  14,
    'A wraith-like assassin born from pure darkness.',
    phase_strike,
    '30% chance each turn to ignore player DEF entirely.').

boss_pool(b5, cursed_champion,  140,  30,  12,
    'A warrior consumed by dark energy.',
    cursed_strikes,
    'Each hit applies a -1 ATK debuff on the player that stacks.').

boss_pool(b6, iron_colossus,    200,  22,  24,
    'A living statue of animated iron.',
    fortified,
    'DEF cannot be reduced below 8 no matter what.').

boss_pool(b7, plague_witch,     120,  26,  10,
    'A diseased sorceress dripping with toxins.',
    poison_cloud,
    'Player loses 4 HP at the start of each of their turns.').

boss_pool(b8, void_herald,      160,  32,  16,
    'A herald of nothingness from beyond the veil.',
    void_drain,
    'Drains 5 HP from the player and heals itself for 5 each turn.').

% Final boss — always floor 5, fixed, terrifying.
final_boss(labyrinth_overlord, 350, 50, 30,
    'The supreme consciousness of the maze itself. Utterly merciless.',
    absolute_dominion,
    'Raises ATK by 3 every 2 turns. Heals 10 HP when player uses an item. Ignores 40% of player DEF.').

% --- 6. SHRINE BUFFS ---
shrine_buff(s1, 'Altar of Strength',  attack,  4).
shrine_buff(s2, 'Altar of Iron',      defense, 4).
shrine_buff(s3, 'Healing Fountain',   hp,      20).
shrine_buff(s4, 'Whispering Statue',  attack,  3).
shrine_buff(s5, 'Ward of Protection', defense, 3).

% --- 7. FLOOR LAYOUT GENERATION ---
% Guarantees: 2 combat, 1 loot, 1 shrine, 1 rest, 1 skill room.
generate_floor(Rooms) :-
    findall(R-T, room_type(R, _, T), All),
    include([_-combat]>>(true), All, Combats),
    include([_-loot]>>(true),   All, Loots),
    include([_-shrine]>>(true), All, Shrines),
    include([_-rest]>>(true),   All, Rests),
    include([_-skill]>>(true),  All, Skills),
    random_member(C1-_, Combats),
    random_member(C2-_, Combats), C2 \= C1,
    random_member(L1-_, Loots),
    random_member(S1-_, Shrines),
    random_member(Rt-_, Rests),
    random_member(Sk-_, Skills),
    Rooms = [C1, C2, L1, S1, Rt, Sk].

% Random boss from pool for floors 1-4
random_boss(Name, HP, Atk, Def, Desc, Passive, PassiveDesc) :-
    findall(b(N,H,A,D,Ds,P,Pd),
            boss_pool(_,N,H,A,D,Ds,P,Pd), All),
    random_member(b(Name,HP,Atk,Def,Desc,Passive,PassiveDesc), All).

% --- 8. SKILL FETCH ---
% Returns 3 distinct random skills from the pool.
random_skills(S1, S2, S3) :-
    findall(sk(ID,N,K,D), player_skill(ID,N,K,D), All),
    random_member(sk(_,N1,K1,D1), All),
    random_member(sk(_,N2,K2,D2), All), K2 \= K1,
    random_member(sk(_,N3,K3,D3), All), K3 \= K1, K3 \= K2,
    S1 = sk(N1,K1,D1), S2 = sk(N2,K2,D2), S3 = sk(N3,K3,D3).
