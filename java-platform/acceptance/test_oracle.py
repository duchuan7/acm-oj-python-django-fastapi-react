import unittest
from oracle import rank

START = "2026-01-01T00:00:00Z"


def attempt(ident, user, problem, minute, verdict, score):
    return {"id":ident,"user_id":user,"problem_id":problem,
            "submitted_at":f"2026-01-01T00:{minute:02}:00Z",
            "expected_verdict":verdict,"expected_score":score}


class OracleTest(unittest.TestCase):
    def test_acm_penalty_and_tie_order(self):
        records = [attempt(1,1,10,1,"WRONG_ANSWER",0),attempt(2,1,10,5,"ACCEPTED",100),
                   attempt(3,3,10,4,"ACCEPTED",100),attempt(4,2,10,4,"ACCEPTED",100)]
        rows = rank("ACM",records,START,{10:100})
        self.assertEqual([(r["user_id"],r["penalty_minutes"]) for r in rows],[(2,4),(3,4),(1,25)])

    def test_ioi_weighted_partial_score(self):
        records = [attempt(1,1,10,1,"WRONG_ANSWER",50),attempt(2,1,11,2,"ACCEPTED",100),
                   attempt(3,2,10,2,"ACCEPTED",100)]
        rows = rank("IOI",records,START,{10:40,11:60})
        self.assertEqual([(r["user_id"],r["score"],r["solved"]) for r in rows],[(1,80,2),(2,40,1)])

    def test_freeze_excludes_cutoff_and_later_attempts(self):
        records=[attempt(1,1,10,1,"WRONG_ANSWER",0),attempt(2,1,10,2,"ACCEPTED",100)]
        row=rank("ACM",records,START,{10:100},"2026-01-01T00:02:00Z")[0]
        self.assertEqual((row["solved"],row["penalty_minutes"]),(0,0))


if __name__=="__main__":
    unittest.main()
