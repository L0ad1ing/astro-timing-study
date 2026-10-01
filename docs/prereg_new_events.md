# Pre-registration — new event types (written before running)

Event types: Prize, Job_Start, Job_End, Trial (Relationship_Begin/End have <150 training sets: reported as
too few). Training half only; 5-fold person-grouped CV; model = src/models.py PARAMS (age clock excluded).

Primary endpoint: window test top-3 hit rate (chance 15%), valid only if the placebo window test passes and
the mismatched-chart C is <= 0.52.

Expectations (mine): the within-person C-index is 0.50-0.54 for each type; no type's window top-3 lower
95% bound exceeds 15% (sample sizes of 300-700 give intervals of roughly +/-3 to 4 points). A type that
beats chance must also beat its placebo window. With 4 types tested, one nominal "pass" is plausible by
chance alone.
