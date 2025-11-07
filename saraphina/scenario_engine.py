#!/usr/bin/env python3
"""
Scenario Engine and Monte Carlo Planner
- Runs "what if" simulations for a given goal
- Produces futures with probabilities, risk, and reward
"""
from __future__ import annotations
import json
import random
from typing import Dict, Any, List
from datetime import datetime, time as dtime

class ScenarioEngine:
    def __init__(self, conn, risk_model, planner):
        self.conn = conn
        self.risk = risk_model
        self.planner = planner
        
    def simulate_tree(self, goal: str, context: Dict[str, Any], depth: int = 2, branching: int = 3) -> Dict[str, Any]:
        """Shallow policy-aware tree search over constraints variations.
        Returns best paths with aggregate utility.
        """
        depth = max(1, min(3, int(depth)))
        branching = max(1, min(5, int(branching)))
        paths = []
        # Seed nodes: random samples of env constraints
        seeds = []
        for _ in range(branching):
            env = self._sample_env()
            seeds.append({'devices': len(env['devices']), 'policies': len(env['policies'])})
        def utility(o):
            return o['prob'] * (o['reward'] - 0.5*o['risk'])
        best = []
        for s in seeds:
            cur_constraints = s
            agg_util = 0.0
            steps = []
            for d in range(depth):
                # Vary constraints slightly
                var = dict(cur_constraints)
                var['devices'] = max(0, var['devices'] + random.choice([-1,0,1]))
                var['policies'] = max(0, var['policies'] + random.choice([-1,0,1]))
                plan = self.planner.plan(goal, context, var)
                main_action = plan['steps'][0] if plan.get('steps') else goal
                base_conf = float(plan.get('confidence', 0.6))
                # Policy penalty density
                density_penalty = min(0.2, 0.01 * var['policies'])
                reward = max(0.0, base_conf - density_penalty + random.uniform(-0.04, 0.04))
                risk = self._risk_score(main_action)
                prob = max(0.05, min(0.98, reward * (1.0 - 0.5 * risk)))
                u = prob * (reward - 0.5*risk)
                agg_util += u
                steps.append({'constraints': var, 'u': u, 'plan': plan})
                cur_constraints = var
            best.append({'seed': s, 'agg_utility': agg_util/float(depth), 'steps': steps})
        best.sort(key=lambda x: x['agg_utility'], reverse=True)
        return {'goal': goal, 'mode': 'tree', 'depth': depth, 'branching': branching, 'paths': best[:5]}

    def _sample_env(self) -> Dict[str, Any]:
        """Sample environment state from DB (devices/policies), with randomness."""
        cur = self.conn.cursor()
        # devices
        try:
            cur.execute("SELECT device_id, name, last_seen FROM devices")
            devices = [dict(r) for r in cur.fetchall()]
        except Exception:
            devices = []
        # policies
        try:
            cur.execute("SELECT device_id, policy_json FROM device_policies")
            policies = [dict(r) for r in cur.fetchall()]
        except Exception:
            policies = []
        # Random drop to simulate intermittency
        d_keep = [d for d in devices if random.random() > 0.2]
        p_keep = [p for p in policies if random.random() > 0.1]
        # Parse policy JSON safely
        parsed_policies: List[Dict[str, Any]] = []
        for p in p_keep:
            try:
                pj = p.get('policy_json')
                if isinstance(pj, str):
                    import json as _json
                    pj = _json.loads(pj)
                parsed_policies.append({'device_id': p.get('device_id'), **(pj or {})})
            except Exception:
                parsed_policies.append({'device_id': p.get('device_id')})
        return {
            'devices': d_keep,
            'policies': parsed_policies,
            'time': datetime.utcnow().isoformat()
        }

    def _risk_score(self, action_desc: str) -> float:
        r = self.risk.assess(action_desc)
        lvl = r.get('level', 'safe')
        if lvl == 'safe': return 0.1
        if lvl == 'caution': return 0.5
        return 0.9

    def _policy_penalties(self, policies: List[Dict[str, Any]], now: datetime, goal: str) -> Dict[str, float]:
        """Compute aggregate penalty/boost from current policies."""
        reward_penalty = 0.0
        risk_boost = 0.0
        violations = 0
        hhmm = now.strftime('%H:%M')
        for pol in policies:
            # Bedtime blocks after a certain hour
            try:
                bt = pol.get('bed_time')
                if bt and isinstance(bt, str) and hhmm >= bt:
                    reward_penalty += 0.05
                    risk_boost += 0.05
                    violations += 1
            except Exception:
                pass
            # Explicit no-exec
            if pol.get('no_exec') is True:
                reward_penalty += 0.1
                risk_boost += 0.1
                violations += 1
            # Goal-keyword throttles
            try:
                keywords = pol.get('throttle_keywords') or []
                if isinstance(keywords, list) and any(k.lower() in goal.lower() for k in keywords):
                    reward_penalty += 0.05
            except Exception:
                pass
        return {'reward_penalty': min(0.3, reward_penalty), 'risk_boost': min(0.3, risk_boost), 'violations': violations}

    def simulate(self, goal: str, context: Dict[str, Any], trials: int = 200) -> Dict[str, Any]:
        """Run Monte Carlo simulation for a goal; returns ranked outcomes with probabilities."""
        trials = max(50, min(1000, int(trials)))
        outcomes: List[Dict[str, Any]] = []
        for t in range(trials):
            env = self._sample_env()
            constraints = {'devices': len(env['devices']), 'policies': len(env['policies'])}
            plan = self.planner.plan(goal, context, constraints)
            # Policy-aware adjustments
            now = datetime.utcnow()
            pen = self._policy_penalties(env['policies'], now, goal)
            # Utility model
            base_conf = float(plan.get('confidence', 0.6))
            density_penalty = min(0.2, 0.01 * constraints['policies'])
            reward = max(0.0, base_conf - density_penalty - pen['reward_penalty'] + random.uniform(-0.05, 0.05))
            # Risk from main action + policy boost
            main_action = plan['steps'][0] if plan.get('steps') else goal
            risk = min(0.99, self._risk_score(main_action) + pen['risk_boost'])
            # Success probability
            prob = max(0.05, min(0.98, reward * (1.0 - 0.5 * risk)))
            outcomes.append({'plan': plan, 'env': {**constraints, 'policy_violations': pen['violations']}, 'reward': reward, 'risk': risk, 'prob': prob})
        # Cluster outcomes into simple buckets by (risk,reward)
        def bucket(o):
            r = 'low' if o['risk'] < 0.25 else 'med' if o['risk'] < 0.6 else 'high'
            w = 'low' if o['reward'] < 0.4 else 'med' if o['reward'] < 0.7 else 'high'
            return f"risk:{r}|reward:{w}"
        buckets: Dict[str, Dict[str, Any]] = {}
        for o in outcomes:
            k = bucket(o)
            b = buckets.setdefault(k, {'count':0, 'avg_prob':0.0, 'avg_risk':0.0, 'avg_reward':0.0, 'sample_plan': o['plan']})
            b['count'] += 1
            b['avg_prob'] += o['prob']
            b['avg_risk'] += o['risk']
            b['avg_reward'] += o['reward']
        ranked = []
        for k, b in buckets.items():
            n = float(b['count'])
            ranked.append({
                'bucket': k,
                'probability': b['avg_prob']/n,
                'risk': b['avg_risk']/n,
                'reward': b['avg_reward']/n,
                'sample_plan': b['sample_plan']
            })
        ranked.sort(key=lambda x: (x['probability'] * (x['reward'] - 0.5*x['risk'])), reverse=True)
        # top raw outcomes summary
        top = sorted(outcomes, key=lambda x: (x['prob'] * (x['reward'] - 0.5*x['risk'])), reverse=True)[:5]
        return {
            'goal': goal,
            'trials': trials,
            'ranked_buckets': ranked[:5],
            'top_samples': [{
                'prob': o['prob'], 'risk': o['risk'], 'reward': o['reward'], 'plan': o['plan']
            } for o in top]
        }
