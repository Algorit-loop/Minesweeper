# minesweeper/ai/ai.py
import random
from collections import defaultdict, deque

# Lưu ý: Không dùng typing kiểu mới để tương thích Python 3.8+

class MinesweeperAI:
    """
    AI Minesweeper: CSP + subset + exact enumeration theo thành phần nhỏ.
    Giao diện:
      - next_actions(board) -> {"flags": [(r,c),...], "reveal": [(r,c),...]}
      - guess(board) -> (r,c)  # gọi sau next_actions nếu chưa có nước đi chắc chắn
    """

    def __init__(self, enum_limit=16):
        # Số biến tối đa trong 1 component để liệt kê nghiệm chính xác (an toàn & nhanh).
        self.enum_limit = enum_limit
        self._best_guess = None  # ghi nhớ sau next_actions

    # ----------------- PUBLIC API -----------------
    def next_actions(self, board):
        self._best_guess = None

        # 1) Thu ràng buộc từ các ô số đã mở
        constraints = self._build_constraints(board)  # list[{"vars": set[(r,c)], "sum": int}]

        # 2) Lặp suy luận đơn + subset tới bão hòa
        known_safe = set()
        known_mine = set()
        changed = True
        while changed:
            changed = False

            # 2.1 single-point: nếu sum==0 -> tất cả SAFE; nếu sum==|vars| -> tất cả MINE
            safes, mines = self._trivial(constraints)
            if safes or mines:
                changed = True
                known_safe.update(safes)
                known_mine.update(mines)
                self._apply_known(constraints, safes, mines)

            # 2.2 subset inference: A ⊂ B ⇒ B\A có tổng = sum(B)-sum(A)
            if self._subset_infer(constraints, known_safe, known_mine):
                changed = True
                # sau khi sinh thêm ràng buộc đơn, áp lại trivial
                safes, mines = self._trivial(constraints)
                if safes or mines:
                    known_safe.update(safes)
                    known_mine.update(mines)
                    self._apply_known(constraints, safes, mines)
                    changed = True

        if known_safe or known_mine:
            return {"flags": sorted(list(known_mine)), "reveal": sorted(list(known_safe))}

        # 3) Chia thành phần độc lập theo biến giao nhau
        comps = self._components(constraints)

        # 4) Exact enumeration trên component nhỏ -> tính P(mine) cho từng biến
        probs = {}
        for comp_constraints, comp_vars in comps:
            k = len(comp_vars)
            if k == 0:
                continue
            if k <= self.enum_limit:
                comp_probs = self._exact_probabilities(comp_constraints, comp_vars)
                # gom kết quả
                probs.update(comp_probs)

        # 5) Nếu có ô chắc chắn (P=0 hoặc P=1) -> trả luôn
        safes = [v for v, p in probs.items() if p <= 1e-12]
        mines = [v for v, p in probs.items() if p >= 1.0 - 1e-12]
        if safes or mines:
            return {"flags": sorted(mines), "reveal": sorted(safes)}

        # 6) Nếu chưa có nước đi chắc chắn, chọn ô có P nhỏ nhất để đoán
        if probs:
            best_v, best_p = None, 9e9
            for v, p in probs.items():
                if p < best_p:
                    best_v, best_p = v, p
            self._best_guess = best_v
            return {"flags": [], "reveal": []}

        # 7) Không tính được P (không có ràng buộc): đoán ô biên “giàu thông tin”
        self._best_guess = self._border_guess(board)
        return {"flags": [], "reveal": []}

    def guess(self, board):
        if self._best_guess is not None:
            return self._best_guess
        return self._border_guess(board)

    # ----------------- BUILD CONSTRAINTS -----------------
    def _build_constraints(self, board):
        constraints = []
        seen = set()
        for r in range(board.rows):
            for c in range(board.cols):
                cell = board.grid[r][c]
                if not cell.revealed:
                    continue
                n = cell.adj
                if n < 0:
                    continue
                neigh = list(board.neighbors(r, c))
                flagged = [(rr, cc) for (rr, cc) in neigh if board.is_flagged(rr, cc)]
                hidden = [(rr, cc) for (rr, cc) in neigh if (not board.is_revealed(rr, cc) and not board.is_flagged(rr, cc))]
                rem = n - len(flagged)
                if rem < 0:
                    rem = 0
                if hidden:
                    key = (frozenset(hidden), rem)
                    if key not in seen:
                        seen.add(key)
                        constraints.append({"vars": set(hidden), "sum": rem})
        return constraints

    # ----------------- INFERENCE CORE -----------------
    def _trivial(self, constraints):
        safes, mines = set(), set()
        for c in constraints:
            V, s = c["vars"], c["sum"]
            if not V:
                continue
            if s == 0:
                safes |= set(V)
            elif s == len(V):
                mines |= set(V)
        return safes, mines

    def _apply_known(self, constraints, safes, mines):
        i = 0
        while i < len(constraints):
            c = constraints[i]
            if not c["vars"]:
                i += 1
                continue
            # xóa biến đã biết và điều chỉnh tổng
            dec = 0
            new_vars = set()
            for v in c["vars"]:
                if v in safes:
                    # mine=0 -> chỉ bỏ biến
                    continue
                elif v in mines:
                    # mine=1 -> sum giảm 1
                    dec += 1
                    continue
                else:
                    new_vars.add(v)
            c["vars"] = new_vars
            c["sum"] -= dec
            # nếu rỗng mà sum != 0 thì mâu thuẫn -> bỏ
            if not c["vars"] and c["sum"] != 0:
                constraints.pop(i)
            else:
                i += 1
        # khử trùng lặp
        self._dedup(constraints)

    def _subset_infer(self, constraints, known_safe, known_mine):
        changed = False
        if len(constraints) < 2:
            return False
        # sắp theo kích thước để dễ xét A ⊂ B
        constraints.sort(key=lambda c: len(c["vars"]))
        n = len(constraints)
        for i in range(n):
            A = constraints[i]
            VA, sA = A["vars"], A["sum"]
            if not VA:
                continue
            for j in range(i + 1, n):
                B = constraints[j]
                VB, sB = B["vars"], B["sum"]
                if not VB or VA == VB:
                    continue
                if VA.issubset(VB):
                    diff = VB - VA
                    if not diff:
                        continue
                    k = sB - sA
                    if k == 0:
                        # diff all safe
                        known_safe |= diff
                        # thêm ràng buộc mới rõ ràng để trivial bắt được
                        constraints.append({"vars": set(diff), "sum": 0})
                        changed = True
                    elif k == len(diff):
                        # diff all mines
                        known_mine |= diff
                        constraints.append({"vars": set(diff), "sum": len(diff)})
                        changed = True
        if changed:
            self._dedup(constraints)
        return changed

    def _dedup(self, constraints):
        seen = {}
        out = []
        for c in constraints:
            key = (frozenset(c["vars"]), c["sum"])
            if key not in seen:
                seen[key] = c
        out.extend(seen.values())
        constraints[:] = out

    # ----------------- COMPONENT SPLIT -----------------
    def _components(self, constraints):
        # map biến -> constraint indices
        var2idx = defaultdict(set)
        for idx, c in enumerate(constraints):
            for v in c["vars"]:
                var2idx[v].add(idx)

        visited_var = set()
        comps = []
        for v in list(var2idx.keys()):
            if v in visited_var:
                continue
            q = deque([v])
            comp_vars = set([v])
            comp_cidx = set()
            visited_var.add(v)
            while q:
                x = q.popleft()
                for ci in var2idx[x]:
                    if ci not in comp_cidx:
                        comp_cidx.add(ci)
                        for y in constraints[ci]["vars"]:
                            if y not in visited_var:
                                visited_var.add(y)
                                comp_vars.add(y)
                                q.append(y)
            comp_constraints = [constraints[i] for i in comp_cidx]
            comps.append((comp_constraints, comp_vars))
        return comps

    # ----------------- EXACT ENUMERATION (BACKTRACK) -----------------
    def _exact_probabilities(self, comp_constraints, comp_vars):
        """
        Trả về dict[var -> P(var là mìn)] cho 1 component nhỏ.
        """
        vars_list = list(comp_vars)
        index_of = {v: i for i, v in enumerate(vars_list)}

        # Ràng buộc theo chỉ số biến
        C = []
        for c in comp_constraints:
            idxs = [index_of[v] for v in c["vars"]]
            C.append({"idxs": idxs, "sum": c["sum"]})

        # Trạng thái ràng buộc
        assigned_sum = [0] * len(C)
        remaining_cnt = [len(c["idxs"]) for c in C]
        appear_in = [[] for _ in range(len(vars_list))]
        for ci, c in enumerate(C):
            for vi in c["idxs"]:
                appear_in[vi].append(ci)

        # Sắp biến theo độ “ràng buộc” giảm dần
        order = list(range(len(vars_list)))
        order.sort(key=lambda vi: -len(appear_in[vi]))

        def feasible(ci):
            s = assigned_sum[ci]
            r = remaining_cnt[ci]
            t = C[ci]["sum"]
            return (s <= t) and (s + r >= t)

        # DFS đếm số nghiệm (và số nghiệm có vi=1)
        mine_solutions = [0] * len(vars_list)

        def dfs_count(pos):
            if pos == len(order):
                # kiểm tra chặt
                for ci in range(len(C)):
                    if assigned_sum[ci] != C[ci]["sum"]:
                        return 0
                return 1

            vi = order[pos]
            total_here = 0

            # val = 0
            touched = []
            ok = True
            for ci in appear_in[vi]:
                remaining_cnt[ci] -= 1
                touched.append(ci)
                if not feasible(ci):
                    ok = False
                    break
            if ok:
                total_here += dfs_count(pos + 1)
            for ci in touched:
                remaining_cnt[ci] += 1

            # val = 1
            touched = []
            ok = True
            for ci in appear_in[vi]:
                remaining_cnt[ci] -= 1
                assigned_sum[ci] += 1
                touched.append(ci)
                if not feasible(ci):
                    ok = False
                    break
            if ok:
                sols_1 = dfs_count(pos + 1)
                total_here += sols_1
                mine_solutions[vi] += sols_1
            for ci in touched:
                assigned_sum[ci] -= 1
                remaining_cnt[ci] += 1

            return total_here

        total = dfs_count(0)
        probs = {}
        if total <= 0:
            # hiếm khi rơi vào mâu thuẫn do trạng thái “bất khả” (cứ trả 0.5 trung lập)
            for v in vars_list:
                probs[v] = 0.5
        else:
            for pos, v in enumerate(vars_list):
                probs[v] = float(mine_solutions[pos]) / float(total)
        return probs

    # ----------------- GUESSES -----------------
    def _border_guess(self, board):
        """
        Nếu không có ràng buộc, chọn ô ẩn sát biên (kề ô đã mở) để sinh thông tin;
        nếu không có biên, chọn ngẫu nhiên trong ô ẩn.
        """
        unknown = [(r, c) for (r, c) in board.unknown_cells()]
        if not unknown:
            return None

        border = []
        for (r, c) in unknown:
            near = 0
            for (rr, cc) in board.neighbors(r, c):
                if board.is_revealed(rr, cc):
                    near += 1
            border.append((near, (r, c)))

        border.sort(key=lambda x: -x[0])
        best_near = border[0][0]
        best = [cell for near, cell in border if near == best_near]
        return random.choice(best)
