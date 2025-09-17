import random

class MinesweeperAI:
    """
    AI áp dụng luật xác định cơ bản:
    - Nếu ô số n có F cờ và H ô ẩn lân cận:
        + Nếu F == n  -> tất cả H còn lại là an toàn (reveal)
        + Nếu F + H == n -> tất cả H là mìn (flag)
    Nếu không suy luận thêm được: đoán một ô có "nguy cơ" thấp gần các ràng buộc.
    """
    def __init__(self):
        pass

    def next_actions(self, board):
        flags = set()
        reveals = set()

        progress = True
        # Lặp áp dụng luật cho đến khi không thay đổi (nhưng chỉ trả về tập kết quả cuối cùng; main sẽ áp dụng)
        while progress:
            progress = False
            for (r, c) in list(board.numbers_cells()):
                n = board.adj_mines(r, c)
                neigh = list(board.neighbors(r, c))
                flagged = [(rr, cc) for (rr, cc) in neigh if board.is_flagged(rr, cc)]
                hidden  = [(rr, cc) for (rr, cc) in neigh if (not board.is_revealed(rr, cc) and not board.is_flagged(rr, cc))]

                F = len(flagged)
                H = len(hidden)

                if H == 0:
                    continue

                # All hidden are safe
                if F == n and H > 0:
                    for cell in hidden:
                        if cell not in reveals and not board.is_revealed(*cell):
                            reveals.add(cell)
                            progress = True

                # All hidden are mines
                if F + H == n and H > 0:
                    for cell in hidden:
                        if cell not in flags and not board.is_flagged(*cell):
                            flags.add(cell)
                            progress = True

        return {"flags": list(flags), "reveal": list(reveals)}

    def guess(self, board):
        """
        Đoán một ô: heuristic đơn giản
        - Ưu tiên ô ẩn gần các ô số (vì có ràng buộc), tính điểm nguy cơ ~ sum(n/(H)) từ các ô số kề.
        - Nếu không có ràng buộc nào, chọn ngẫu nhiên trong các ô ẩn.
        """
        candidates = list(board.unknown_cells())
        if not candidates:
            return None

        # Compute risk score
        scores = []
        for (r, c) in candidates:
            risk = 0.0
            for (rr, cc) in board.neighbors(r, c):
                if board.is_revealed(rr, cc) and board.adj_mines(rr, cc) > 0:
                    n = board.adj_mines(rr, cc)
                    neigh = list(board.neighbors(rr, cc))
                    flagged = sum(1 for (a,b) in neigh if board.is_flagged(a,b))
                    hidden  = sum(1 for (a,b) in neigh if (not board.is_revealed(a,b) and not board.is_flagged(a,b)))
                    # estimated remaining mines around this number
                    rem = max(0, n - flagged)
                    if hidden > 0:
                        risk += rem / hidden
            scores.append((risk, (r, c)))

        scores.sort(key=lambda x: x[0])
        # pick the minimal risk cell; break ties randomly among lowest few
        k = min(5, len(scores))
        subset = scores[:k]
        return random.choice(subset)[1]
