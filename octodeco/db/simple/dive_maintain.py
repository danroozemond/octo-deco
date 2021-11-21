from sqlite3 import Connection
import time;

class DBDiveMaintainer:
    AGE_TO_REMOVE = 0.2;  # days (=~5 hrs)
    MAX_NR_TO_REMOVE = 10;
    RUN_FREQUENCY = 300.0;
    last_run_stale_dives = time.time() - RUN_FREQUENCY;

    def _cleanup_stale_dives(self, db: Connection) -> bool:
        # Every now and then, find old ephemeral dives and clean them up
        if time.time() - self.last_run_stale_dives < self.RUN_FREQUENCY:
            return False;
        self.last_run_stale_dives = time.time();
        # Do
        cur = db.cursor();
        cur.execute("""
                    SELECT d.dive_id, julianday()-julianday(d.last_update) as age
                    FROM dives d 
                    WHERE d.is_ephemeral AND age > ?
                    ORDER BY last_update
                    LIMIT ?;
                    """, [ self.AGE_TO_REMOVE, self.MAX_NR_TO_REMOVE ]);
        cur2 = db.cursor();
        for row in cur:
            dive_id = row['dive_id'];
            cur2.execute("DELETE FROM dives WHERE dive_id = ?", [ dive_id ] );
            print(f'Removed stale dive {dive_id}')

    def go(self, db: Connection):
        self._cleanup_stale_dives(db);
