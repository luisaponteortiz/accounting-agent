How to read this, with RD and RF always measured back to back under the same conditions:

| Condition | RD checkpoint (s) | Delivered RF (s) |
| --- | --- | --- |
| Quiet machine (last block, load average 3.6) | 3.83 to 4.47 | 2.06 to 2.32 |
| Machine still settling after the searches (first block, load average 16; headed "idle" in the raw file, but it was not) | 7.78 to 20.66 | 2.77 to 3.47 |
| 8 busy processes added | 8.10 to 17.58 | 2.55 to 3.99 |
| 16 busy processes added | 10.63 to 25.77, twice not within 60 | 2.76 to 8.80 (two of eight above 5.0) |

The delivered setup is faster than RD's in every pairing, about half the time on a quiet machine, so the cost is below the RD level and not merely back to it. The RE checkpoint, measured once in the first block, took 11.06 to 19.59 seconds where the delivered code took about 3. Inside the real suite the HTTP class setup took 2.36 to 3.39 seconds in the five consecutive runs (next table). With sixteen extra busy processes the delivered setup can still exceed five seconds; RD exceeded it in every loaded measurement, so this is the test's known sensitivity to machine load and not something this pass introduced.
