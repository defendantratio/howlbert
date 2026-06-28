PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE packs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                alpha_id INTEGER,
                treasury INTEGER NOT NULL DEFAULT 0,
                tax_rate INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            , pack_unity INTEGER NOT NULL DEFAULT 5, key TEXT, last_feedall_day INTEGER NOT NULL DEFAULT 0, last_drinkall_day INTEGER NOT NULL DEFAULT 0, last_pack_event_day INTEGER NOT NULL DEFAULT 0, season_stash_deposits INTEGER NOT NULL DEFAULT 0, season_stash_goal_met INTEGER NOT NULL DEFAULT 0, season_goal_epoch INTEGER NOT NULL DEFAULT 0, last_cat_pact_gift_day INTEGER NOT NULL DEFAULT 0, last_garden_tend_day INTEGER NOT NULL DEFAULT 0);
INSERT INTO packs VALUES(1,'Greyspire',NULL,0,0,'2026-06-27T18:53:48.825141+00:00',8,'greyspire',0,0,0,0,0,7,0,0);
INSERT INTO packs VALUES(2,'Mistmoor',NULL,0,0,'2026-06-27T18:53:48.825141+00:00',5,'mistmoor',0,0,0,0,0,0,0,0);
INSERT INTO packs VALUES(3,'Thistlehide',NULL,0,0,'2026-06-27T18:53:48.825141+00:00',6,'thistlehide',0,0,500,0,0,0,0,0);
INSERT INTO packs VALUES(4,'Silverrush',NULL,0,0,'2026-06-27T18:53:48.825141+00:00',5,'silverrush',0,0,0,0,0,0,0,0);
CREATE TABLE world_state (
                guild_id INTEGER PRIMARY KEY,
                day_number INTEGER NOT NULL DEFAULT 1,
                season TEXT NOT NULL DEFAULT 'spring',
                weather TEXT NOT NULL DEFAULT 'clear',
                time_of_day TEXT NOT NULL DEFAULT 'dawn',
                last_rollover TEXT NOT NULL
            , plot_phase INTEGER NOT NULL DEFAULT 0, last_den_news_dm_day INTEGER NOT NULL DEFAULT 0);
INSERT INTO world_state VALUES(999002,1,'spring','clear','dawn','2026-06-27T20:18:46.635176+00:00',4,0);
INSERT INTO world_state VALUES(999003,1,'spring','clear','dawn','2026-06-27T20:18:46.676873+00:00',4,0);
INSERT INTO world_state VALUES(999004,1,'spring','clear','dawn','2026-06-27T20:18:46.700369+00:00',6,0);
INSERT INTO world_state VALUES(999005,1,'spring','clear','dawn','2026-06-27T20:18:46.739419+00:00',11,0);
INSERT INTO world_state VALUES(999007,1,'spring','clear','dawn','2026-06-27T20:18:46.777210+00:00',7,0);
INSERT INTO world_state VALUES(999008,1,'spring','clear','dawn','2026-06-27T20:18:46.847234+00:00',5,0);
INSERT INTO world_state VALUES(999009,1,'spring','clear','dawn','2026-06-27T20:18:46.891441+00:00',3,0);
INSERT INTO world_state VALUES(999010,1,'spring','clear','dawn','2026-06-27T20:18:46.923583+00:00',11,0);
INSERT INTO world_state VALUES(999991,1,'spring','clear','dawn','2026-06-27T20:18:46.587631+00:00',5,0);
INSERT INTO world_state VALUES(1516980863911329802,100,'spring','clear','dawn','2026-06-27T18:53:49.580283+00:00',0,0);
CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                price INTEGER NOT NULL,
                sell_price INTEGER NOT NULL DEFAULT 0
            );
INSERT INTO items VALUES(1,'herb_bundle','Herb Bundle','Use `/bones action:use item:herb_bundle`; random common herbs (2-4) added to `/bones action:inventory`.',40,12);
INSERT INTO items VALUES(2,'prey_bundle','Prey Bundle','Use `/bones action:use item:prey_bundle`; random carcasses (2-3) added to `/food`.',55,18);
INSERT INTO items VALUES(3,'vitality_salve','Vitality Salve','Neonatal care; buy from `/bones action:shop`, then `/pupcare action:save name:<pup>` on the **same sunrise** a lethal-at-birth pup is born to keep them alive.',550,150);
INSERT INTO items VALUES(4,'lucky_tooth','Lucky Tooth','Passive: +15% bones on `/bones action:hunt` while carried.',75,20);
INSERT INTO items VALUES(5,'den_charm','Den Charm','Use `/bones action:use item:den_charm`; +1 pack unity once per rollover (must be in a pack).',100,30);
INSERT INTO items VALUES(6,'rabbit_pelt','Rabbit Pelt','Use `/bones action:use item:rabbit_pelt recipient:@wolf`; trade for +2 standing; they gain 10 bones.',55,15);
INSERT INTO items VALUES(7,'extra_paw','An Extra Paw','Add RP to `/bones action:work` or `/bones action:crime`: your own `scene:` text, or `staff:true` for admin-written flavor (uses one).',150,40);
INSERT INTO items VALUES(8,'safe_roll','Safe Roll','🎲 `/rpg action:roll use_safe_roll:true`; reroll a failed d20 once. **Cannot** be used in combat.',100,30);
INSERT INTO items VALUES(9,'revive','Revive','Use `/bones action:use item:revive` when your active wolf is **dead**; same name & stats, back at 1 HP. Old-age deaths reset to 60 moons. **Ko-fi shop only**.',0,0);
INSERT INTO items VALUES(10,'reincarnation','Reincarnation','Use `/bones action:use item:reincarnation new_name:<name>` when **dead**; new name & juvenile age (12 moons), but keep attributes, skills, standing & bones. Clears prey/toys. **Ko-fi shop only**.',0,0);
INSERT INTO items VALUES(11,'herb_adders_tongue','Adder''s Tongue','Reroll failed poison save with advantage if within 1 minute.',0,5);
INSERT INTO items VALUES(12,'herb_alder_bark','Alder Bark','Cures toothache and gum inflammation.',0,5);
INSERT INTO items VALUES(13,'herb_arnica','Arnica','Halves bruise/sprain recovery (external only).',0,5);
INSERT INTO items VALUES(14,'herb_beech_leaves','Beech Leaves','Carry herbs; nut oil prevents infection 24h.',0,5);
INSERT INTO items VALUES(15,'herb_bindweed','Bindweed Vines','Vines lash straight sticks around a broken leg to set the break; with comfrey −1 week healing.',0,5);
INSERT INTO items VALUES(16,'herb_blackberry','Blackberry (Bramble)','Soothes insect stings; ends non-magical venom poison.',0,5);
INSERT INTO items VALUES(17,'herb_bloodroot','Bloodroot','3d6 poison damage (DC 16 half).',0,5);
INSERT INTO items VALUES(18,'herb_boneset','Boneset','Reroll failed disease save with advantage; take better. Slows early rabies (one sunrise, no cure).',0,5);
INSERT INTO items VALUES(19,'herb_borage','Borage','Extra milk for nursing mother; one additional pup.',0,5);
INSERT INTO items VALUES(20,'herb_broom','Broom','Bind broken bones; move at half speed without worsening.',0,5);
INSERT INTO items VALUES(21,'herb_burdock_root','Burdock Root','Poultice removes infection after 24h rest.',0,5);
INSERT INTO items VALUES(22,'herb_burnet','Burnet','1 leaf/day ignores first exhaustion from forced march.',0,5);
INSERT INTO items VALUES(23,'herb_catchweed','Catchweed Burrs','Holds poultices; extends duration 4 hours.',0,5);
INSERT INTO items VALUES(24,'herb_cattail','Cattail','Stops bleeding like yarrow.',0,5);
INSERT INTO items VALUES(25,'herb_celandine','Celandine','Removes minor eye blindness within 1 hour.',0,5);
INSERT INTO items VALUES(26,'herb_chamomile','Chamomile','Advantage on Wisdom saves vs fear for 1 hour.',0,5);
INSERT INTO items VALUES(27,'herb_chervil','Chervil','Removes nausea; eases redscratch itch.',0,5);
INSERT INTO items VALUES(28,'herb_chickweed','Chickweed','Ends whitecough (3 doses/24h).',0,5);
INSERT INTO items VALUES(29,'herb_cobnuts','Cobnuts','+1 Stealth when approaching prey.',0,5);
INSERT INTO items VALUES(30,'herb_cobwebs','Cobwebs','Auto-stabilize dying wolf; bandages deep gashes.',0,5);
INSERT INTO items VALUES(31,'herb_coltsfoot','Coltsfoot','Ends whitecough after 1 dose.',0,5);
INSERT INTO items VALUES(32,'herb_comfrey','Comfrey','Poultice heals 1d4 HP on deep wounds.',0,5);
INSERT INTO items VALUES(33,'herb_coneflower','Coneflower (Echinacea)','Advantage on infection saves within 1h of injury.',0,5);
INSERT INTO items VALUES(34,'herb_daisy','Daisy','Ignore arthritis pain penalties 8 hours.',0,5);
INSERT INTO items VALUES(35,'herb_dandelion','Dandelion','Soothes stings; reduces headache pain.',0,5);
INSERT INTO items VALUES(36,'herb_deadly_nightshade','Deadly Nightshade','Confusion then paralysis (Wis DC 15).',0,5);
INSERT INTO items VALUES(37,'herb_deathberries','Deathberries (Yew)','Mercy killing; Medic knowledge only.',0,5);
INSERT INTO items VALUES(38,'herb_dried_skullcap','Dried Skullcap','Sedative rest for concussion recovery.',0,5);
INSERT INTO items VALUES(39,'herb_dock','Dock','Restores cracked paw pads after 1 day rest.',0,5);
INSERT INTO items VALUES(40,'herb_douglas_sagewort','Douglas'' Sagewort','Prevents infection 24h; advantage vs fear 1h.',0,5);
INSERT INTO items VALUES(41,'herb_edelweiss','Edelweiss','Ends bellyache; suppresses cough 4h.',0,5);
INSERT INTO items VALUES(42,'herb_elder','Elder (external)','Treats sprains; toxic if eaten (DC 14 or 2d4 poison).',0,5);
INSERT INTO items VALUES(43,'herb_elderberry','Elderberry','Advantage on disease saves for 3 sunrises.',0,5);
INSERT INTO items VALUES(44,'herb_fennel','Fennel','Extra day without food before exhaustion.',0,5);
INSERT INTO items VALUES(45,'herb_feverfew','Feverfew','Advantage on disease saves for 1 day.',0,5);
INSERT INTO items VALUES(46,'herb_foxglove','Foxglove','Deadly heart poison (DC 18 or die in 1d4 min).',0,5);
INSERT INTO items VALUES(47,'herb_goldenrod','Goldenrod','+2 HP per 8h rest. Slows early rabies (+2 next save, no cure).',0,5);
INSERT INTO items VALUES(48,'herb_heather','Heather','Sweetens bitter herb mixtures.',0,5);
INSERT INTO items VALUES(49,'herb_holly_berries','Holly Berries','2d4 poison (DC 12 half).',0,5);
INSERT INTO items VALUES(50,'herb_honey','Honey','Feeds starving pups (+10 hunger, −1 exhaustion); sweetens `/pupcare action:feed`. Adults: −1 starvation exhaustion when depleted.',0,5);
INSERT INTO items VALUES(51,'herb_horsetail','Horsetail','+3 Medicine to stabilize dying.',0,5);
INSERT INTO items VALUES(52,'herb_ivy_vines','Ivy Vines','Preserves dried herbs 2 extra weeks.',0,5);
INSERT INTO items VALUES(53,'herb_jewelweed','Jewelweed','Touch-me-not sap neutralizes poison-ivy rash; cools bee and nettle stings.',0,5);
INSERT INTO items VALUES(54,'herb_juniper_berry','Juniper Berries','Cures mild poison or nausea.',0,5);
INSERT INTO items VALUES(55,'herb_knotgrass','Knotgrass','Cures diarrhea; kills worms/fleas in 1 day.',0,5);
INSERT INTO items VALUES(56,'herb_labrador_tea','Labrador Tea','Ends wheezing for 4 hours.',0,5);
INSERT INTO items VALUES(57,'herb_lambs_ear','Lamb''s Ear','Advantage on disease saves until next sunrise.',0,5);
INSERT INTO items VALUES(58,'herb_lavender','Lavender','Cures fever/chills; hides death-scent at burial.',0,5);
INSERT INTO items VALUES(59,'herb_mullein','Mullein','Heals yellowcough and rot-lung lung damage; Medics use it for full recovery.',0,5);
INSERT INTO items VALUES(60,'herb_lungwort','Lungwort','Also heals yellowcough and rot-lung when mullein is scarce.',0,5);
INSERT INTO items VALUES(61,'herb_marsh_mallow','Marsh-Mallow Root','Soothes rot-lung fever and wheeze; prized by Mistmoor healers.',0,5);
INSERT INTO items VALUES(62,'herb_belly_rip_fungus','Belly-Rip Fungus','Glow-fungus from the Belly-Rip sinkhole; only cure for rot-lung necrosis.',0,5);
INSERT INTO items VALUES(63,'herb_lizards_tail','Lizard''s Tail','Removes 1 fever exhaustion.',0,5);
INSERT INTO items VALUES(64,'herb_meadowsweet','Meadowsweet','Ignore 1 pain exhaustion 4h.',0,5);
INSERT INTO items VALUES(65,'herb_mountain_ash','Mountain Ash (Rowan)','Bitter bark eases fever and hard-pad distemper.',0,5);
INSERT INTO items VALUES(66,'herb_oak_bark','Oak Bark','Stops bleeding; +2 stabilize.',0,5);
INSERT INTO items VALUES(67,'herb_oleander','Oleander','4d6 poison, no antidote (DC 18 half).',0,5);
INSERT INTO items VALUES(68,'herb_parsley','Parsley','Ends lactation within 6 hours; eases milk-fever.',0,5);
INSERT INTO items VALUES(69,'herb_passionflower','Passionflower','Eases racing thoughts and nightmare sleep.',0,5);
INSERT INTO items VALUES(70,'herb_pine_needle','Pine Needles','Tea ends coughing after 1 dose.',0,5);
INSERT INTO items VALUES(71,'herb_pine_bark','Pine Bark','Inner bark strips ease Leaf-bare cough and frost-nipped paws; Greyspire medics peel it in cold weather.',0,5);
INSERT INTO items VALUES(72,'herb_plantain','Plantain','Gentle wound remedy.',0,5);
INSERT INTO items VALUES(73,'herb_poison_ivy','Poison Ivy','Contact: −1d4 CHA, disadvantage Stealth 3 days.',0,5);
INSERT INTO items VALUES(74,'herb_poppy_seeds','Poppy Seeds','Sedative and pain relief; unconscious rest 1 sunrise.',0,5);
INSERT INTO items VALUES(75,'herb_prickly_ash','Prickly Ash','Ends frozen-paw numbness; numbs tooth pain 1h.',0,5);
INSERT INTO items VALUES(76,'herb_purple_loosestrife','Purple Loosestrife','Staunches bleeding on stitched wounds; reduces bleed timer; cures diarrhea.',0,5);
INSERT INTO items VALUES(77,'herb_ragweed','Ragweed','3 leaves removes 1 exhaustion.',0,5);
INSERT INTO items VALUES(78,'herb_ragwort','Ragwort','Elder hunts at full speed for 1 day.',0,5);
INSERT INTO items VALUES(79,'herb_raspberry_leaves','Raspberry Leaves','Advantage on birth hemorrhage saves.',0,5);
INSERT INTO items VALUES(80,'herb_rosemary','Rosemary','Hides death-scent at burial.',0,5);
INSERT INTO items VALUES(81,'herb_rush_stalks','Rush Stalks','Hard stalks bind broken bones; lash splints with sticks (+2 Medicine to set fractures).',0,5);
INSERT INTO items VALUES(82,'herb_saffron','Saffron','Auto-stabilize postpartum hemorrhage; ends milk-fever.',0,5);
INSERT INTO items VALUES(83,'herb_sage','Sage','Soothes sore throat; elders eat hard food longer.',0,5);
INSERT INTO items VALUES(84,'herb_skunk_cabbage','Skunk Cabbage (dried)','Treats severe cough; toxic if fresh (DC 12).',0,5);
INSERT INTO items VALUES(85,'herb_slippery_elm','Slippery Elm','Eat/drink without pain 8 hours.',0,5);
INSERT INTO items VALUES(86,'herb_snakeroot','Snakeroot','Advantage vs snake venom saves.',0,5);
INSERT INTO items VALUES(87,'herb_sorrel','Sorrel','Stops heavy bleeding; restores appetite.',0,5);
INSERT INTO items VALUES(88,'stick','Straight Stick','Thin twig for wolves in pain to bite during deep treatment; also used to lash splints.',0,5);
INSERT INTO items VALUES(89,'herb_sticklewort','Sticklewort','Neutralizes snake venom if within 1 minute.',0,5);
INSERT INTO items VALUES(90,'herb_stinging_nettle','Stinging Nettle','With comfrey +1 broken bone healing.',0,5);
INSERT INTO items VALUES(91,'herb_swamp_milkweed','Swamp Milkweed','Breaks curses; cures deadly disease.',0,5);
INSERT INTO items VALUES(92,'herb_sweet_sedge','Sweet Sedge','Ends mild gut infection in 1 day; steadies Belly-Rip tremors.',0,5);
INSERT INTO items VALUES(93,'herb_tansy','Tansy','Halves sprain recovery time.',0,5);
INSERT INTO items VALUES(94,'herb_thyme','Thyme','Ends minor pain 2 hours.',0,5);
INSERT INTO items VALUES(95,'herb_tormentil','Tormentil','+2 Medicine for any injury.',0,5);
INSERT INTO items VALUES(96,'herb_valerian','Valerian','Calms shock; unconscious 1d4 hours.',0,5);
INSERT INTO items VALUES(97,'herb_watermint','Watermint','Removes nausea in 10 minutes.',0,5);
INSERT INTO items VALUES(98,'herb_water_hemlock','Water Hemlock','Lethal poison (DC 20 half, still 6d6).',0,5);
INSERT INTO items VALUES(99,'herb_wild_cherry_bark','Wild Cherry Bark','Stops coughing 2 hours, even blackcough.',0,5);
INSERT INTO items VALUES(100,'herb_wild_garlic','Wild Garlic','Advantage vs vermin disease 24h.',0,5);
INSERT INTO items VALUES(101,'herb_willow_bark','Willow Bark','Pain relief 1 sunrise; cools marsh fever.',0,5);
INSERT INTO items VALUES(102,'herb_wintergreen','Wintergreen','Often misidentified; 1d4 poison (DC 10).',0,5);
INSERT INTO items VALUES(103,'herb_witch_hazel','Witch Hazel','Astringent: reduces swelling; soothes insect stings and bruises; eases eye strain.',0,5);
INSERT INTO items VALUES(104,'herb_wolfsbane','Wolfsbane','Removes spirit curse (DC 20 Med); 2d6 poison to patient.',0,5);
INSERT INTO items VALUES(105,'herb_yarrow','Yarrow','+2 Medicine to stabilize; stops bleeding.',0,5);
INSERT INTO items VALUES(106,'herb_catmint','Catmint Tea','Cures severe blackcough (2 doses/24h); eases anxiety.',0,5);
INSERT INTO items VALUES(107,'herb_purslane','Purslane','Fleshy leaves hold ditch-water; chew for +12 thirst without visiting the creek.',0,5);
INSERT INTO items VALUES(108,'herb_chicory','Chicory','Bitter roadside root; settles a gut upset by garbage or nerves.',0,5);
INSERT INTO items VALUES(109,'herb_mugwort','Mugwort','Gravel-ditch mugwort; rub through pelt to drive off fleas.',0,5);
INSERT INTO items VALUES(110,'herb_garden_mint','Garden Mint','Escaped from a Twoleg herb bed; ends nausea in minutes.',0,5);
INSERT INTO items VALUES(111,'herb_wood_sorrel','Wood Sorrel','Sour shamrock in mowed lawn; steadies a queasy stomach after edging too close.',0,5);
INSERT INTO items VALUES(112,'herb_oxeye_daisy','Oxeye Daisy','Thunderpath-margin daisy; eases joint ache like its meadow kin.',0,5);
INSERT INTO items VALUES(113,'herb_common_mallow','Common Mallow','Soft leaves in roadside dust; mild poultice for scraped pads.',0,5);
INSERT INTO items VALUES(114,'herb_shepherds_purse','Shepherd''s Purse','Triangular seed-pods along the gravel; slows oozing cuts.',0,5);
INSERT INTO items VALUES(115,'herb_garlic_mustard','Garlic Mustard','Invasive roadside mustard; rub through pelt to drive off fleas.',0,5);
INSERT INTO items VALUES(116,'prey_vole','Vole Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~4 sunrises. Buy at the trading post.',18,4);
INSERT INTO items VALUES(117,'prey_hare','Hare Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~5 sunrises. Buy at the trading post.',38,10);
INSERT INTO items VALUES(118,'prey_rabbit','Rabbit Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~5 sunrises. Buy at the trading post.',32,8);
INSERT INTO items VALUES(119,'prey_fish','River Fish','Hoard carcass; `/eat` or `/preypile`. Rots after ~4 sunrises. Buy at the trading post.',30,8);
INSERT INTO items VALUES(120,'prey_grouse','Grouse Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~5 sunrises. Buy at the trading post.',48,14);
INSERT INTO items VALUES(121,'prey_agouti','Agouti Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~5 sunrises.',0,0);
INSERT INTO items VALUES(122,'prey_beaver','Beaver Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~6 sunrises.',0,0);
INSERT INTO items VALUES(123,'prey_deer','Deer Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~7 sunrises.',0,0);
INSERT INTO items VALUES(124,'prey_elk','Elk Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~8 sunrises.',0,0);
INSERT INTO items VALUES(125,'prey_carrion','Old Carrion','Hoard carcass; `/eat` or `/preypile`. Rots after ~3 sunrises.',0,0);
INSERT INTO items VALUES(126,'prey_coyote','Coyote Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~5 sunrises.',0,0);
INSERT INTO items VALUES(127,'prey_fox','Fox Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~4 sunrises.',0,0);
INSERT INTO items VALUES(128,'prey_badger','Badger Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~6 sunrises.',0,0);
INSERT INTO items VALUES(129,'prey_wolverine','Wolverine Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~6 sunrises.',0,0);
INSERT INTO items VALUES(130,'prey_cougar','Cougar Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~7 sunrises.',0,0);
INSERT INTO items VALUES(131,'prey_black_bear','Black Bear Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~8 sunrises.',0,0);
INSERT INTO items VALUES(132,'prey_grizzly_bear','Grizzly Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~8 sunrises.',0,0);
INSERT INTO items VALUES(133,'prey_feral_dog','Feral Hearth-hound Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~5 sunrises.',0,0);
INSERT INTO items VALUES(134,'prey_guard_dog','Guard Hearth-hound Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~5 sunrises.',0,0);
INSERT INTO items VALUES(135,'prey_hunting_dog','Hunting Hearth-hound Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~5 sunrises.',0,0);
INSERT INTO items VALUES(136,'prey_fighting_dog','Fighting Hearth-hound Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~5 sunrises.',0,0);
INSERT INTO items VALUES(137,'prey_cat_carcass','Cat Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~4 sunrises.',0,0);
INSERT INTO items VALUES(138,'prey_kittypet_carcass','Kittypet Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~3 sunrises.',0,0);
INSERT INTO items VALUES(139,'prey_wolf_carcass','Wolf Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~6 sunrises.',0,0);
INSERT INTO items VALUES(140,'prey_frog','Frog Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~3 sunrises.',0,0);
INSERT INTO items VALUES(141,'prey_snake','Snake Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~4 sunrises.',0,0);
INSERT INTO items VALUES(142,'prey_lizard','Lizard Carcass','Hoard carcass; `/eat` or `/preypile`. Rots after ~4 sunrises.',0,0);
INSERT INTO items VALUES(143,'prey_berries','Mouthful of Berries','Hoard carcass; `/eat` or `/preypile`. Rots after ~3 sunrises.',0,0);
INSERT INTO items VALUES(144,'prey_windfall_fruit','Windfall Fruit','Hoard carcass; `/eat` or `/preypile`. Rots after ~4 sunrises.',0,0);
INSERT INTO items VALUES(145,'prey_roots','Roots & Tubers','Hoard carcass; `/eat` or `/preypile`. Rots after ~9 sunrises.',0,0);
INSERT INTO items VALUES(146,'prey_forage_greens','Tender Greens','Hoard carcass; `/eat` or `/preypile`. Rots after ~2 sunrises.',0,0);
INSERT INTO items VALUES(147,'toy_bone','Bone','Gnawed clean; classic pack amusement.; `/playpen action:play` to boost mood. Buy at the trading post.',10,2);
INSERT INTO items VALUES(148,'toy_feather','Feather Bundle','Soft plumes to bat around the den.; `/playpen action:play` to boost mood. Buy at the trading post.',14,3);
INSERT INTO items VALUES(149,'toy_acorn','Acorn','A chipmunk''s loss is your pup''s gain.; `/playpen action:play` to boost mood. Buy at the trading post.',8,1);
INSERT INTO items VALUES(150,'toy_shell','Mollusk Shell','Clatters nicely on stone; endless entertainment.; `/playpen action:play` to boost mood. Buy at the trading post.',12,2);
INSERT INTO items VALUES(151,'toy_talon','Owl Talon','Sharp, shiny, forbidden; wolves love it.; `/playpen action:play` to boost mood. Buy at the trading post.',20,5);
INSERT INTO items VALUES(152,'toy_stick','Chew Stick','Splintered branch from an old den site.; `/playpen action:play` to boost mood. Buy at the trading post.',10,2);
CREATE TABLE quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                objective_type TEXT NOT NULL,
                objective_count INTEGER NOT NULL DEFAULT 1,
                reward_bones INTEGER NOT NULL DEFAULT 0,
                standing_reward INTEGER NOT NULL DEFAULT 0,
                quest_type TEXT NOT NULL DEFAULT 'static',
                difficulty TEXT NOT NULL DEFAULT 'easy'
            , required_role TEXT, required_pack TEXT);
INSERT INTO quests VALUES(1,'first_hunt','First Blood','Complete your first hunt and bring meat back to the den.','hunt',1,50,5,'unique','easy',NULL,NULL);
INSERT INTO quests VALUES(2,'den_patrol','Border Patrol','Walk the pack border and watch for rival scent.','patrol',1,35,3,'static','easy',NULL,NULL);
INSERT INTO quests VALUES(3,'river_fish','River Rations','Catch fish from the Silverrush shallows.','fishing',1,40,3,'static','easy',NULL,NULL);
INSERT INTO quests VALUES(4,'triple_tracker','Master Tracker','Follow three separate scent trails to their source.','track',3,120,10,'static','medium',NULL,NULL);
INSERT INTO quests VALUES(5,'den_gift','Feed the Treasury','Deposit 50 bones into your pack treasury.','deposit',50,60,8,'static','medium',NULL,NULL);
INSERT INTO quests VALUES(6,'biome_wander','Range the Wild','Venture beyond the den; dig, follow scent, or investigate the biome.','explore',1,30,3,'static','easy',NULL,NULL);
INSERT INTO quests VALUES(7,'trail_seeker','Old Trails','Explore the wild three separate sunrises.','explore',3,90,8,'static','medium',NULL,NULL);
INSERT INTO quests VALUES(8,'blink_border_patrol','White Omen Patrol','Walk the border while the moon is bitten; report what you scent.','patrol',1,45,4,'static','easy',NULL,NULL);
INSERT INTO quests VALUES(9,'blink_river_crisis','Warm Shallows','Fish the river twice while the water runs wrong.','fishing',2,55,5,'static','medium',NULL,NULL);
INSERT INTO quests VALUES(10,'blink_wind_witness','Wind Witness','Read the wind on a paranoid border sunrise.','sniff',1,40,4,'static','easy',NULL,NULL);
INSERT INTO quests VALUES(11,'blink_mill_scout','Mill Scout','Range the wild and investigate what sleeps under the mill road.','explore',1,70,6,'static','medium',NULL,NULL);
INSERT INTO quests VALUES(12,'blink_ash_naming','Ash Naming Howl','Sing the remembered name to the pack three sunrises.','howl',3,80,8,'static','medium',NULL,NULL);
INSERT INTO quests VALUES(13,'blink_rogue_ledger','Edge Ledger','Run two scores on the border while packs blame each other (rogues).','crime',2,65,5,'static','medium',NULL,NULL);
INSERT INTO quests VALUES(14,'blink_healer_listen','Ear to the Wind','Read the bitten moon by sound while The Blinking begins.','sniff',1,40,4,'static','easy',NULL,NULL);
INSERT INTO quests VALUES(15,'blink_healer_touch','Healer''s Touch','Treat wounds twice while the den runs hot with injuries.','treat',2,55,5,'static','medium',NULL,NULL);
INSERT INTO quests VALUES(16,'hunter_first_blood','Prove the Kill','Bring down prey with your jaws alone; the pack watches hunters.','hunt',2,70,5,'role','easy','hunter',NULL);
INSERT INTO quests VALUES(17,'medic_healer_path','Poultice for the Den','Tend the wounded; use `/medic action:treat` with a herb or `/medic action:stabilize` a dying packmate.','treat',1,55,6,'role','easy','medic',NULL);
INSERT INTO quests VALUES(18,'scout_border_eyes','Eyes on the Ridge','Walk the border unseen. Report what moves in rival scent.','patrol',2,65,5,'role','medium','scout',NULL);
INSERT INTO quests VALUES(19,'scout_biome_eyes','Read the Land','Rescout your biome after ranging out; read what the wild left behind.','explore',2,55,5,'role','easy','scout',NULL);
INSERT INTO quests VALUES(20,'scout_wind_survey','Wind on the Ridge','Survey the border and report what moves; `/scout survey`.','survey',3,65,6,'role','medium','scout',NULL);
INSERT INTO quests VALUES(21,'scout_trail_hunter','Cold Trail','Follow sign off the main paths; `/scout trail`.','trail',3,70,5,'role','medium','scout',NULL);
INSERT INTO quests VALUES(22,'guard_den_watch','Night at the Entrance','Stand watch while the den sleeps.','patrol',2,60,6,'role','medium','guard',NULL);
INSERT INTO quests VALUES(23,'forager_root_seeker','Roots in the Rain','Find what the forest offers after the storm.','forage',2,50,4,'role','easy','forager',NULL);
INSERT INTO quests VALUES(24,'diplomat_peace_talk','Words Before Teeth','Mediate tension before it becomes blood.','patrol',1,55,8,'role','medium','diplomat',NULL);
INSERT INTO quests VALUES(25,'elder_memory_howl','Howl the Old Names','Speak the names of wolves the land still remembers.','patrol',1,45,7,'role','easy','elder',NULL);
INSERT INTO quests VALUES(26,'caretaker_pup_watch','Pups in the Storm','Keep the young ones calm through foul weather.','patrol',1,40,6,'role','easy','caretaker',NULL);
INSERT INTO quests VALUES(27,'alpha_den_judgment','Alpha''s Judgment','Settle a dispute before the den fractures.','deposit',25,80,10,'role','hard','alpha',NULL);
INSERT INTO quests VALUES(28,'advisor_alpha_shadow','Walk in the Alpha''s Shadow','Counsel the pack while the Alpha hunts.','patrol',2,70,7,'role','medium','advisor',NULL);
INSERT INTO quests VALUES(29,'drown_belly_vigil','Vigil at the Belly-Rip','Sit at the dark water until the chewing speaks. Mistmoor tradition.','patrol',1,75,10,'role','medium','drown_sick','mistmoor');
INSERT INTO quests VALUES(30,'drown_moon_prophecy','When the Eye Blinks','Watch the Maw''s moon until meaning finds you.','patrol',1,90,12,'role','hard','drown_sick','mistmoor');
INSERT INTO quests VALUES(31,'drown_whisper_stone','The Sundering Stone','Find the carved prophecy in neutral ground; if the land lets you.','track',1,100,15,'unique','hard','drown_sick',NULL);
INSERT INTO quests VALUES(32,'pup_first_moon','Survive the First Moon','Live through the first moon unnamed; then earn your name at the ceremony.','patrol',1,35,5,'role','easy','pup',NULL);
INSERT INTO quests VALUES(33,'pup_den_warmth','Stay in the Nursery','Rest close to caretakers while the adults hunt.','patrol',2,30,4,'role','easy','pup',NULL);
INSERT INTO quests VALUES(34,'juvenile_blooding','The Blooding','Kill a rabbit or larger prey alone to prove you can earn an adult role.','hunt',1,80,8,'role','medium','juvenile',NULL);
INSERT INTO quests VALUES(35,'juvenile_rank_patrol','Border Yearling','Walk the juvenile patrol route without crying a challenge howl.','patrol',2,55,5,'role','easy','juvenile',NULL);
INSERT INTO quests VALUES(36,'juvenile_practice_hunt','Practice Kill','Complete hunts on live training prey assigned by the den.','hunt',2,70,6,'role','medium','juvenile',NULL);
CREATE TABLE user_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                quest_id INTEGER NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                assigned_day INTEGER NOT NULL DEFAULT 0,
                accepted_at TEXT NOT NULL,
                completed_at TEXT, wolf_id INTEGER,
                FOREIGN KEY (quest_id) REFERENCES quests(id)
            );
CREATE TABLE territories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                name TEXT NOT NULL,
                owner_pack_id INTEGER,
                daily_bonus INTEGER NOT NULL DEFAULT 5,
                UNIQUE (guild_id, key),
                FOREIGN KEY (owner_pack_id) REFERENCES packs(id)
            );
CREATE TABLE wars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                territory_id INTEGER NOT NULL,
                attacker_pack_id INTEGER NOT NULL,
                defender_pack_id INTEGER,
                start_day INTEGER NOT NULL,
                end_day INTEGER NOT NULL,
                attacker_score INTEGER NOT NULL DEFAULT 0,
                defender_score INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (territory_id) REFERENCES territories(id),
                FOREIGN KEY (attacker_pack_id) REFERENCES packs(id)
            );
CREATE TABLE account_progress (
                discord_id INTEGER PRIMARY KEY,
                legacy_score INTEGER NOT NULL DEFAULT 0,
                prestige_tier INTEGER NOT NULL DEFAULT 0,
                total_quests INTEGER NOT NULL DEFAULT 0,
                total_hunts INTEGER NOT NULL DEFAULT 0,
                total_retirements INTEGER NOT NULL DEFAULT 0
            , xp INTEGER NOT NULL DEFAULT 0, autoproxy_wolf_id INTEGER, active_wolf_id INTEGER, used_secondary_switch INTEGER NOT NULL DEFAULT 0, boost_first_claimed INTEGER NOT NULL DEFAULT 0, boost_second_claimed INTEGER NOT NULL DEFAULT 0, invite_reward_month TEXT NOT NULL DEFAULT '', invite_reward_count INTEGER NOT NULL DEFAULT 0, donor_tier TEXT NOT NULL DEFAULT '', donor_total_cents INTEGER NOT NULL DEFAULT 0, donor_supporter_until TEXT NOT NULL DEFAULT '', donor_bones_month TEXT NOT NULL DEFAULT '', donor_bones_month_amount INTEGER NOT NULL DEFAULT 0, kickstarter_backer INTEGER NOT NULL DEFAULT 0, kofi_membership_tier TEXT NOT NULL DEFAULT '', kofi_membership_until TEXT NOT NULL DEFAULT '', possess_wolf_id INTEGER);
CREATE TABLE retired_wolves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                wolf_name TEXT NOT NULL,
                great_pack TEXT,
                legacy_contribution INTEGER NOT NULL,
                retired_at TEXT NOT NULL
            );
CREATE TABLE prey_piles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER,
            hunter_wolf_id INTEGER NOT NULL,
            hunter_name TEXT NOT NULL,
            prey_label TEXT NOT NULL,
            prey_bones INTEGER NOT NULL DEFAULT 0,
            day_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        );
CREATE TABLE prey_pile_responses (
            pile_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            choice TEXT NOT NULL,
            responded_at TEXT NOT NULL,
            PRIMARY KEY (pile_id, wolf_id),
            FOREIGN KEY (pile_id) REFERENCES prey_piles(id)
        );
CREATE TABLE prey_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            prey_key TEXT NOT NULL,
            uses_left INTEGER NOT NULL,
            bone_value INTEGER NOT NULL,
            acquired_day INTEGER NOT NULL,
            is_rotting INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        );
CREATE TABLE herb_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            herb_key TEXT NOT NULL,
            form TEXT NOT NULL DEFAULT 'fresh',
            acquired_day INTEGER NOT NULL,
            potency INTEGER NOT NULL DEFAULT 100,
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        );
CREATE TABLE herb_seeds (
            wolf_id INTEGER NOT NULL,
            herb_key TEXT NOT NULL,
            qty INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (wolf_id, herb_key),
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        );
CREATE TABLE herb_gardens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            herb_key TEXT NOT NULL,
            planted_day INTEGER NOT NULL,
            season_planted TEXT NOT NULL DEFAULT 'spring',
            last_tended_day INTEGER NOT NULL DEFAULT 0,
            last_eval_day INTEGER NOT NULL DEFAULT 0,
            health INTEGER NOT NULL DEFAULT 100,
            dead INTEGER NOT NULL DEFAULT 0, pack_id INTEGER,
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        );
CREATE TABLE wolf_death_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            discord_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            guild_id INTEGER,
            cause TEXT NOT NULL,
            day INTEGER,
            logged_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        );
CREATE TABLE collab_hunts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER,
            leader_wolf_id INTEGER NOT NULL,
            pack_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            result_text TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
CREATE TABLE collab_hunt_members (
            hunt_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            discord_id INTEGER NOT NULL,
            joined_at TEXT NOT NULL DEFAULT (datetime('now')),
            hunt_role TEXT NOT NULL DEFAULT 'flank',
            rp_said INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (hunt_id, wolf_id),
            FOREIGN KEY (hunt_id) REFERENCES collab_hunts(id)
        );
CREATE TABLE collab_patrols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER,
            leader_wolf_id INTEGER NOT NULL,
            pack_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            result_text TEXT,
            patrol_kind TEXT NOT NULL DEFAULT 'survey',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
CREATE TABLE collab_patrol_members (
            patrol_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            discord_id INTEGER NOT NULL,
            joined_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (patrol_id, wolf_id),
            FOREIGN KEY (patrol_id) REFERENCES collab_patrols(id)
        );
CREATE TABLE IF NOT EXISTS "users" (id INTEGER PRIMARY KEY AUTOINCREMENT, wolf_name TEXT NOT NULL, pack_id INTEGER, rank TEXT NOT NULL DEFAULT 'subordinate', strength INTEGER NOT NULL DEFAULT 10, speed INTEGER NOT NULL DEFAULT 10, stamina INTEGER NOT NULL DEFAULT 10, scent INTEGER NOT NULL DEFAULT 10, standing INTEGER NOT NULL DEFAULT 0, bones INTEGER NOT NULL DEFAULT 0, condition TEXT NOT NULL DEFAULT 'healthy', last_hunt_day INTEGER NOT NULL DEFAULT 0, last_daily_day INTEGER NOT NULL DEFAULT 0, last_hunt TEXT, last_daily TEXT, created_at TEXT NOT NULL, last_scavenge_day INTEGER NOT NULL DEFAULT 0, last_track_day INTEGER NOT NULL DEFAULT 0, last_fishing_day INTEGER NOT NULL DEFAULT 0, great_pack TEXT, deposit_progress INTEGER NOT NULL DEFAULT 0, last_patrol_day INTEGER NOT NULL DEFAULT 0, last_scout_day INTEGER NOT NULL DEFAULT 0, wolf_role TEXT NOT NULL DEFAULT 'hunter', attr_str INTEGER NOT NULL DEFAULT 6, attr_dex INTEGER NOT NULL DEFAULT 5, attr_con INTEGER NOT NULL DEFAULT 4, attr_int INTEGER NOT NULL DEFAULT 1, attr_cha INTEGER NOT NULL DEFAULT 1, attr_wis INTEGER NOT NULL DEFAULT 1, skill_proficiencies TEXT NOT NULL DEFAULT '[]', hp INTEGER NOT NULL DEFAULT 11, max_hp INTEGER NOT NULL DEFAULT 11, exhaustion INTEGER NOT NULL DEFAULT 0, active_injuries TEXT NOT NULL DEFAULT '[]', disease TEXT, last_forage_day INTEGER NOT NULL DEFAULT 0, last_verge_forage_day INTEGER NOT NULL DEFAULT 0, last_rest_day INTEGER NOT NULL DEFAULT 0, herb_heals_today INTEGER NOT NULL DEFAULT 0, herb_treats_today INTEGER NOT NULL DEFAULT 0, gender TEXT, birth_sex TEXT, sexuality TEXT NOT NULL DEFAULT 'bisexual', is_pregnant INTEGER NOT NULL DEFAULT 0, pregnancy_start_day INTEGER NOT NULL DEFAULT 0, mate_discord_id INTEGER, death_save_round INTEGER NOT NULL DEFAULT 0, death_save_fails INTEGER NOT NULL DEFAULT 0, death_save_successes INTEGER NOT NULL DEFAULT 0, cause_of_death TEXT, death_day INTEGER, receptive_day INTEGER NOT NULL DEFAULT 0, bonus_role_feature TEXT, character_traits TEXT, maw_belief TEXT, character_lore TEXT, avatar_url TEXT, pronouns TEXT, ref_image_url TEXT, bio TEXT, birthday TEXT, proxy_prefix TEXT, proxy_suffix TEXT, bonded_mate_id INTEGER, last_adopt_day INTEGER NOT NULL DEFAULT 0, last_den_charm_day INTEGER NOT NULL DEFAULT 0, last_hunt_yield INTEGER NOT NULL DEFAULT 0, last_prey_pile_day INTEGER NOT NULL DEFAULT 0, last_prey_label TEXT, last_role_event_day INTEGER NOT NULL DEFAULT 0, last_prophecy_day INTEGER NOT NULL DEFAULT 0, last_role_reroll_day INTEGER NOT NULL DEFAULT 0, commanding_howl_buff INTEGER NOT NULL DEFAULT 0, last_blood_oath_day INTEGER NOT NULL DEFAULT 0, scout_hidden_day INTEGER NOT NULL DEFAULT 0, hunger_exhaustion_skip INTEGER NOT NULL DEFAULT 0, march_exhaustion_skip INTEGER NOT NULL DEFAULT 0, jaw_meal_shield INTEGER NOT NULL DEFAULT 0, smoke_debuff INTEGER NOT NULL DEFAULT 0, last_forager_gift_day INTEGER NOT NULL DEFAULT 0, quarantined INTEGER NOT NULL DEFAULT 0, genetic_conditions TEXT NOT NULL DEFAULT '[]', disease_save_buff INTEGER NOT NULL DEFAULT 0, cough_suppressed INTEGER NOT NULL DEFAULT 0, milk_fever_due_day INTEGER NOT NULL DEFAULT 0, disease_save_buff_days INTEGER NOT NULL DEFAULT 0, herb_buffs TEXT NOT NULL DEFAULT '{}', distressed INTEGER NOT NULL DEFAULT 0, extra_pup_milk INTEGER NOT NULL DEFAULT 0, last_nurse_day INTEGER NOT NULL DEFAULT 0, last_milk_day INTEGER NOT NULL DEFAULT 0, long_term_injuries TEXT NOT NULL DEFAULT '[]', frightened_fire INTEGER NOT NULL DEFAULT 0, last_fire_reroll_day INTEGER NOT NULL DEFAULT 0, omen_buff TEXT NOT NULL DEFAULT '', last_sacred_day INTEGER NOT NULL DEFAULT 0, food_cache_meals INTEGER NOT NULL DEFAULT 0, last_surgery_day INTEGER NOT NULL DEFAULT 0, bone_rest_until INTEGER NOT NULL DEFAULT 0, last_observe_day INTEGER NOT NULL DEFAULT 0, last_medic_rounds_day INTEGER NOT NULL DEFAULT 0, last_healer_tribute_day INTEGER NOT NULL DEFAULT 0, last_swim_day INTEGER NOT NULL DEFAULT 0, naming_ceremony_day INTEGER NOT NULL DEFAULT 0, skill_ranks TEXT NOT NULL DEFAULT '{}', trait_failure_days TEXT NOT NULL DEFAULT '{}', size_class TEXT NOT NULL DEFAULT '', discord_id INTEGER NOT NULL, mate_wolf_id INTEGER, last_work_day INTEGER NOT NULL DEFAULT 0, last_crime_day INTEGER NOT NULL DEFAULT 0, last_duplicate_trade_day INTEGER NOT NULL DEFAULT 0, last_cat_receive_day INTEGER NOT NULL DEFAULT 0, last_wolf_receive_day INTEGER NOT NULL DEFAULT 0, last_cat_food_trade_day INTEGER NOT NULL DEFAULT 0, last_firepaw_reward_day INTEGER NOT NULL DEFAULT 0, last_soot_reward_day INTEGER NOT NULL DEFAULT 0, last_rivershroud_reward_day INTEGER NOT NULL DEFAULT 0, last_finnpelt_reward_day INTEGER NOT NULL DEFAULT 0, last_plot_witness_day INTEGER NOT NULL DEFAULT 0, last_plot_healer_day INTEGER NOT NULL DEFAULT 0, last_rest_omen_day INTEGER NOT NULL DEFAULT 0, age_months INTEGER NOT NULL DEFAULT 24, last_ageup_day INTEGER NOT NULL DEFAULT 0, birth_lunar_phase TEXT NOT NULL DEFAULT '', last_lunar_aged_lunation INTEGER NOT NULL DEFAULT -1, injury_since TEXT NOT NULL DEFAULT '{}', last_sign_day INTEGER NOT NULL DEFAULT 0, last_sign_read_day INTEGER NOT NULL DEFAULT 0, last_howl_day INTEGER NOT NULL DEFAULT 0, last_sniff_day INTEGER NOT NULL DEFAULT 0, last_mark_day INTEGER NOT NULL DEFAULT 0, sniff_bonus_day INTEGER NOT NULL DEFAULT 0, last_explore_day INTEGER NOT NULL DEFAULT 0, last_play_day INTEGER NOT NULL DEFAULT 0, last_socialize_day INTEGER NOT NULL DEFAULT 0, last_raccoon_day INTEGER NOT NULL DEFAULT 0, raccoon_sells_today INTEGER NOT NULL DEFAULT 0, mood INTEGER NOT NULL DEFAULT 75, last_rescout_day INTEGER NOT NULL DEFAULT 0, last_playall_day INTEGER NOT NULL DEFAULT 0, rescout_uses_today INTEGER NOT NULL DEFAULT 0, last_survey_day INTEGER NOT NULL DEFAULT 0, last_trail_day INTEGER NOT NULL DEFAULT 0, hunger INTEGER NOT NULL DEFAULT 80, thirst INTEGER NOT NULL DEFAULT 80, remnants INTEGER NOT NULL DEFAULT 0, last_groom_day INTEGER NOT NULL DEFAULT 0, last_drink_day INTEGER NOT NULL DEFAULT 0, drinks_today INTEGER NOT NULL DEFAULT 0, last_drink_at TEXT NOT NULL DEFAULT '', last_wild_encounter_day INTEGER NOT NULL DEFAULT 0, last_wild_encounter_at TEXT NOT NULL DEFAULT '', hunt_uses_today INTEGER NOT NULL DEFAULT 0, last_hunt_uses_day INTEGER NOT NULL DEFAULT 0, raccoon_buys_today INTEGER NOT NULL DEFAULT 0, last_raccoon_offer_day INTEGER NOT NULL DEFAULT 0, bio_parent_1_id INTEGER, bio_parent_2_id INTEGER, adopt_parent_1_id INTEGER, adopt_parent_2_id INTEGER, is_born_pup INTEGER NOT NULL DEFAULT 0, has_blooding INTEGER NOT NULL DEFAULT 0, last_court_day INTEGER NOT NULL DEFAULT 0, ic_location TEXT);
INSERT INTO users VALUES(14,'Field',NULL,'subordinate',10,10,10,10,0,0,'healthy',0,0,NULL,NULL,'test',0,0,0,NULL,0,0,0,'hunter',6,5,4,1,1,1,'[]',20,20,0,'[]','mild_poison:stung',0,0,0,0,0,NULL,NULL,'bisexual',0,0,NULL,0,0,0,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,0,0,0,NULL,0,0,0,0,0,0,0,0,0,0,0,0,'[]',0,0,0,0,'{}',0,0,0,0,'[]',0,0,'',0,0,0,0,0,0,0,0,0,'{}','{}','',999400001000000001,NULL,0,0,0,0,0,0,0,0,0,0,0,0,0,24,0,'full_moon',-1,'{}',0,0,0,0,0,0,0,0,0,0,0,75,0,0,0,0,0,80,80,0,0,0,0,'',0,'',0,0,0,0,NULL,NULL,NULL,NULL,0,0,0,NULL);
CREATE TABLE IF NOT EXISTS "inventory" (
            wolf_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (wolf_id, item_id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        );
INSERT INTO inventory VALUES(99044,104,1);
INSERT INTO inventory VALUES(99045,104,1);
INSERT INTO inventory VALUES(99047,104,1);
INSERT INTO inventory VALUES(99048,104,1);
INSERT INTO inventory VALUES(99049,104,1);
CREATE TABLE combat_encounters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'recruiting',
            round INTEGER NOT NULL DEFAULT 0,
            turn_order TEXT NOT NULL DEFAULT '[]',
            current_turn INTEGER NOT NULL DEFAULT 0,
            created_by INTEGER,
            created_at TEXT NOT NULL
        , is_hunt_prey INTEGER NOT NULL DEFAULT 0, hunter_discord_id INTEGER, hunter_wolf_id INTEGER, hunt_prey_rewarded INTEGER NOT NULL DEFAULT 0, ambush_activity TEXT NOT NULL DEFAULT '', ambush_finalized INTEGER NOT NULL DEFAULT 0, is_border_fight INTEGER NOT NULL DEFAULT 0, border_fight_rewarded INTEGER NOT NULL DEFAULT 0, border_cat_clan TEXT NOT NULL DEFAULT '', border_pact_violation INTEGER NOT NULL DEFAULT 0, collab_hunt_id INTEGER, collab_patrol_id INTEGER);
CREATE TABLE combat_fighters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encounter_id INTEGER NOT NULL,
            discord_id INTEGER,
            npc_name TEXT,
            initiative INTEGER NOT NULL DEFAULT 0,
            hp INTEGER NOT NULL,
            max_hp INTEGER NOT NULL, npc_template TEXT, combat_flags TEXT NOT NULL DEFAULT '{}', wolf_id INTEGER,
            FOREIGN KEY (encounter_id) REFERENCES combat_encounters(id)
        );
CREATE TABLE pack_relations (
            guild_id INTEGER NOT NULL,
            pack_a_id INTEGER NOT NULL,
            pack_b_id INTEGER NOT NULL,
            standing INTEGER NOT NULL DEFAULT 5,
            PRIMARY KEY (guild_id, pack_a_id, pack_b_id),
            FOREIGN KEY (pack_a_id) REFERENCES packs(id),
            FOREIGN KEY (pack_b_id) REFERENCES packs(id)
        );
CREATE TABLE pack_raid_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            victim_pack_id INTEGER NOT NULL,
            suspect_pack_id INTEGER NOT NULL,
            stolen_amount INTEGER NOT NULL DEFAULT 0,
            recovered_amount INTEGER NOT NULL DEFAULT 0,
            raid_day INTEGER NOT NULL,
            expires_day INTEGER NOT NULL,
            caught INTEGER NOT NULL DEFAULT 0,
            last_audit_day INTEGER NOT NULL DEFAULT 0,
            accused_pack_id INTEGER,
            accuse_day INTEGER NOT NULL DEFAULT 0
        );
CREATE TABLE bond_relation_cooldowns (
            guild_id INTEGER NOT NULL,
            pack_a_id INTEGER NOT NULL,
            pack_b_id INTEGER NOT NULL,
            last_penalty_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, pack_a_id, pack_b_id)
        );
CREATE TABLE cross_pack_scandals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            wolf_a_id INTEGER NOT NULL,
            wolf_b_id INTEGER NOT NULL,
            pack_a_id INTEGER NOT NULL,
            pack_b_id INTEGER NOT NULL,
            caught_day INTEGER NOT NULL,
            UNIQUE (guild_id, wolf_a_id, wolf_b_id)
        );
CREATE TABLE scent_marks (
            guild_id INTEGER NOT NULL,
            territory_key TEXT NOT NULL,
            pack_key TEXT NOT NULL,
            marker_wolf_id INTEGER NOT NULL,
            marked_day INTEGER NOT NULL,
            PRIMARY KEY (guild_id, territory_key, pack_key),
            FOREIGN KEY (marker_wolf_id) REFERENCES users(id)
        );
CREATE TABLE pack_diplomacy_log (
            guild_id INTEGER NOT NULL,
            pack_a_id INTEGER NOT NULL,
            pack_b_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            action_day INTEGER NOT NULL,
            PRIMARY KEY (guild_id, pack_a_id, pack_b_id, action, action_day),
            FOREIGN KEY (pack_a_id) REFERENCES packs(id),
            FOREIGN KEY (pack_b_id) REFERENCES packs(id)
        );
CREATE TABLE combat_target_picks (
            discord_id INTEGER NOT NULL,
            encounter_id INTEGER NOT NULL,
            target_fighter_id INTEGER NOT NULL,
            PRIMARY KEY (discord_id, encounter_id),
            FOREIGN KEY (encounter_id) REFERENCES combat_encounters(id)
        );
CREATE TABLE pending_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_discord_id INTEGER NOT NULL,
            to_discord_id INTEGER NOT NULL,
            from_item_id INTEGER,
            from_item_qty INTEGER NOT NULL DEFAULT 0,
            from_bones INTEGER NOT NULL DEFAULT 0,
            to_item_id INTEGER,
            to_item_qty INTEGER NOT NULL DEFAULT 0,
            to_bones INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            message_id INTEGER
        );
CREATE TABLE pack_howls (
            pack_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            howl_day INTEGER NOT NULL,
            discord_id INTEGER NOT NULL,
            PRIMARY KEY (pack_id, guild_id, howl_day, discord_id)
        );
CREATE TABLE pack_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            pack_id INTEGER NOT NULL,
            signaler_id INTEGER NOT NULL,
            signal_key TEXT NOT NULL,
            target_id INTEGER,
            day INTEGER NOT NULL,
            responders TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
CREATE TABLE rp_scenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            thread_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            topic TEXT,
            owner_discord_id INTEGER NOT NULL,
            day INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        , roster_message_id INTEGER);
CREATE TABLE rp_scene_members (
            scene_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            discord_id INTEGER NOT NULL,
            joined_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (scene_id, wolf_id)
        );
CREATE TABLE wolf_journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            event_key TEXT NOT NULL,
            summary TEXT NOT NULL,
            day INTEGER,
            guild_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
INSERT INTO wolf_journal_entries VALUES(1,1,'registered','joined the den as **BondWolfA** (Lone).',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(2,2,'registered','joined the den as **BondWolfB** (Lone).',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(3,3,'registered','joined the den as **BirthMother** (Greyspire).',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(4,4,'registered','joined the den as **BirthFather** (Greyspire).',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(5,3,'bonded','bonded with **BirthFather**.',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(6,4,'bonded','bonded with **BirthMother**.',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(7,3,'bonded','bonded with **BirthFather**.',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(8,4,'bonded','bonded with **BirthMother**.',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(9,5,'registered','joined the den as **AdopterOne** (Greyspire).',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(10,6,'registered','joined the den as **AdopterTwo** (Greyspire).',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(11,7,'registered','joined the den as **YouthPup** (Greyspire).',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(12,5,'bonded','bonded with **AdopterTwo**.',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(13,6,'bonded','bonded with **AdopterOne**.',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(14,8,'registered','joined the den as **CourterA** (Greyspire).',NULL,NULL,'2026-06-27 18:53:49');
INSERT INTO wolf_journal_entries VALUES(15,9,'registered','joined the den as **CourterB** (Greyspire).',NULL,NULL,'2026-06-27 18:53:49');
CREATE TABLE app_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
INSERT INTO app_meta VALUES('wolf_journal_backfill_v1','0');
INSERT INTO app_meta VALUES('canonical_bonds_v2','0');
INSERT INTO app_meta VALUES('canonical_mates_v1','0');
INSERT INTO app_meta VALUES('pronoun_backfill_v3','0');
INSERT INTO app_meta VALUES('herb_stacks_to_inventory_v1','0');
CREATE TABLE server_npcs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            avatar_url TEXT,
            bio TEXT,
            proxy_prefix TEXT,
            proxy_suffix TEXT,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(guild_id, name)
        );
CREATE TABLE pending_adoptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER,
            message_id INTEGER,
            adopter_1_wolf_id INTEGER NOT NULL,
            adopter_2_wolf_id INTEGER NOT NULL,
            youth_wolf_id INTEGER NOT NULL,
            youth_owner_discord_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
INSERT INTO pending_adoptions VALUES(1,1516980863911329802,1,NULL,5,6,7,999100005000000005,50,'declined','2026-06-27T18:53:49.800169+00:00');
INSERT INTO pending_adoptions VALUES(2,1516980863911329802,1,NULL,5,6,7,999100005000000005,50,'accepted','2026-06-27T18:53:49.839236+00:00');
CREATE TABLE court_history (
            courter_wolf_id INTEGER NOT NULL,
            target_wolf_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            PRIMARY KEY (courter_wolf_id, target_wolf_id, day_number)
        );
CREATE TABLE wolf_bonds (
            wolf_a_id INTEGER NOT NULL,
            wolf_b_id INTEGER NOT NULL,
            bond_type TEXT NOT NULL,
            strength INTEGER NOT NULL DEFAULT 40,
            note TEXT NOT NULL DEFAULT '',
            created_day INTEGER NOT NULL DEFAULT 0,
            updated_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (wolf_a_id, wolf_b_id, bond_type),
            CHECK (wolf_a_id < wolf_b_id)
        );
INSERT INTO wolf_bonds VALUES(1,2,'rivalry',60,'',11,11);
CREATE TABLE wolf_families (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL COLLATE NOCASE UNIQUE,
            founder_wolf_id INTEGER NOT NULL,
            created_day INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
INSERT INTO wolf_families VALUES(1,'The Howlers 1',1,12,'2026-06-27T18:53:49.086748+00:00');
CREATE TABLE wolf_family_members (
            family_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            joined_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (family_id, wolf_id),
            FOREIGN KEY (family_id) REFERENCES wolf_families(id)
        );
INSERT INTO wolf_family_members VALUES(1,1,'founder',12);
CREATE TABLE pack_cat_pacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            pack_id INTEGER NOT NULL,
            clan_name TEXT NOT NULL COLLATE NOCASE,
            pact_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            trust INTEGER NOT NULL DEFAULT 50,
            tribute_paid INTEGER NOT NULL DEFAULT 0,
            terms_note TEXT NOT NULL DEFAULT '',
            forged_day INTEGER NOT NULL DEFAULT 0,
            expires_day INTEGER NOT NULL DEFAULT 0,
            forged_by_discord_id INTEGER NOT NULL DEFAULT 0,
            broken_day INTEGER,
            break_reason TEXT NOT NULL DEFAULT '',
            UNIQUE(pack_id, clan_name)
        );
CREATE TABLE pack_cat_pact_offers (
            pack_id INTEGER NOT NULL,
            clan_name TEXT NOT NULL COLLATE NOCASE,
            last_fail_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (pack_id, clan_name)
        );
CREATE TABLE pack_wolf_treaties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            pack_id INTEGER NOT NULL,
            other_pack_id INTEGER NOT NULL,
            pact_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            terms_note TEXT NOT NULL DEFAULT '',
            forged_day INTEGER NOT NULL DEFAULT 0,
            expires_day INTEGER NOT NULL DEFAULT 0,
            forged_by_discord_id INTEGER NOT NULL DEFAULT 0,
            broken_day INTEGER,
            break_reason TEXT NOT NULL DEFAULT '',
            UNIQUE(pack_id, other_pack_id)
        );
CREATE TABLE pack_wolf_pact_offers (
            pack_id INTEGER NOT NULL,
            other_pack_id INTEGER NOT NULL,
            last_fail_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (pack_id, other_pack_id)
        );
CREATE TABLE pending_mates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER,
            message_id INTEGER,
            initiator_wolf_id INTEGER NOT NULL,
            partner_wolf_id INTEGER NOT NULL,
            partner_discord_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
INSERT INTO pending_mates VALUES(1,1516980863911329802,1,NULL,8,9,999100007000000007,60,'declined','2026-06-27T18:53:49.940400+00:00');
CREATE TABLE pending_role_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            discord_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            role_feature TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            resolved_by_discord_id INTEGER
        );
CREATE TABLE pending_stillborn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            mother_wolf_id INTEGER NOT NULL,
            pup_name TEXT NOT NULL,
            genetic_conditions TEXT NOT NULL DEFAULT '[]',
            stats_json TEXT NOT NULL,
            father_wolf_id INTEGER,
            pack_id INTEGER,
            great_pack TEXT,
            birth_sex TEXT NOT NULL,
            born_day INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
CREATE TABLE pack_prey_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            prey_key TEXT NOT NULL,
            uses_left INTEGER NOT NULL,
            bone_value INTEGER NOT NULL,
            acquired_day INTEGER NOT NULL,
            is_rotting INTEGER NOT NULL DEFAULT 0,
            deposited_by INTEGER,
            FOREIGN KEY (pack_id) REFERENCES packs(id)
        );
CREATE TABLE pack_herb_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            herb_key TEXT NOT NULL,
            form TEXT NOT NULL DEFAULT 'dried',
            potency INTEGER NOT NULL DEFAULT 100,
            quantity INTEGER NOT NULL DEFAULT 1,
            acquired_day INTEGER NOT NULL,
            deposited_by INTEGER,
            FOREIGN KEY (pack_id) REFERENCES packs(id)
        );
INSERT INTO pack_herb_stacks VALUES(1,1,1,'foxglove','fresh',100,1,10,99044);
INSERT INTO pack_herb_stacks VALUES(2,1,1,'foxglove','fresh',100,1,10,99045);
INSERT INTO pack_herb_stacks VALUES(3,1,1,'foxglove','fresh',100,1,10,99046);
INSERT INTO pack_herb_stacks VALUES(4,1,1,'foxglove','fresh',100,1,10,99047);
INSERT INTO pack_herb_stacks VALUES(5,1,1,'foxglove','fresh',100,1,10,99048);
INSERT INTO pack_herb_stacks VALUES(6,1,1,'foxglove','fresh',100,1,10,99049);
CREATE TABLE pack_amusement_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            uses_left INTEGER NOT NULL,
            deposited_by INTEGER,
            FOREIGN KEY (pack_id) REFERENCES packs(id)
        );
CREATE TABLE amusement_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            uses_left INTEGER NOT NULL,
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        );
CREATE TABLE invite_referrals (
            guild_id INTEGER NOT NULL,
            invitee_discord_id INTEGER NOT NULL,
            inviter_discord_id INTEGER NOT NULL,
            join_day INTEGER NOT NULL,
            registered_day INTEGER,
            rollovers_after_register INTEGER NOT NULL DEFAULT 0,
            welcome_granted INTEGER NOT NULL DEFAULT 0,
            referrer_granted INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, invitee_discord_id)
        );
CREATE TABLE donation_codes (
            code TEXT PRIMARY KEY,
            bones INTEGER NOT NULL DEFAULT 0,
            donor_tier TEXT NOT NULL DEFAULT '',
            mood_bonus INTEGER NOT NULL DEFAULT 0,
            standing_bonus INTEGER NOT NULL DEFAULT 0,
            daily_bonus_days INTEGER NOT NULL DEFAULT 0,
            max_uses INTEGER NOT NULL DEFAULT 1,
            uses_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            note TEXT NOT NULL DEFAULT ''
        );
CREATE TABLE chat_xp_claims (
            discord_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            last_claim_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (discord_id, guild_id)
        );
CREATE TABLE donation_redemptions (
            code TEXT NOT NULL,
            discord_id INTEGER NOT NULL,
            redeemed_at TEXT NOT NULL,
            PRIMARY KEY (code, discord_id)
        );
CREATE TABLE kofi_transactions (
            transaction_id TEXT PRIMARY KEY,
            discord_id INTEGER NOT NULL,
            amount_cents INTEGER NOT NULL,
            bones_granted INTEGER NOT NULL,
            processed_at TEXT NOT NULL,
            event_type TEXT NOT NULL DEFAULT 'donation',
            tier_name TEXT NOT NULL DEFAULT '',
            is_subscription INTEGER NOT NULL DEFAULT 0
        );
CREATE TABLE kofi_email_links (
            email TEXT PRIMARY KEY,
            discord_id INTEGER NOT NULL,
            linked_at TEXT NOT NULL
        );
CREATE TABLE kofi_shop_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL,
            discord_id INTEGER,
            email TEXT NOT NULL DEFAULT '',
            product_key TEXT NOT NULL,
            product_label TEXT NOT NULL,
            amount_cents INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            fulfilled_at TEXT
        );
CREATE TABLE broken_canine_rites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id INTEGER NOT NULL,
            incumbent_wolf_id INTEGER NOT NULL,
            winner_wolf_id INTEGER NOT NULL,
            log_json TEXT NOT NULL,
            outcome TEXT NOT NULL,
            triggered_day INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('users',99049);
INSERT INTO sqlite_sequence VALUES('packs',6);
INSERT INTO sqlite_sequence VALUES('items',3344);
INSERT INTO sqlite_sequence VALUES('quests',792);
INSERT INTO sqlite_sequence VALUES('wolf_journal_entries',15);
INSERT INTO sqlite_sequence VALUES('wolf_families',1);
INSERT INTO sqlite_sequence VALUES('pending_adoptions',2);
INSERT INTO sqlite_sequence VALUES('pending_mates',1);
INSERT INTO sqlite_sequence VALUES('herb_stacks',5);
INSERT INTO sqlite_sequence VALUES('pack_herb_stacks',6);
CREATE INDEX idx_users_discord_id ON users(discord_id);
CREATE INDEX idx_pack_raid_alerts_victim
        ON pack_raid_alerts (guild_id, victim_pack_id, expires_day)
        ;
CREATE INDEX idx_wolf_journal_wolf
        ON wolf_journal_entries (wolf_id, id DESC)
        ;
CREATE UNIQUE INDEX idx_users_wolf_name_ci ON users(wolf_name COLLATE NOCASE);
CREATE UNIQUE INDEX idx_pending_stillborn_pup_name_ci ON pending_stillborn(pup_name COLLATE NOCASE);
COMMIT;
