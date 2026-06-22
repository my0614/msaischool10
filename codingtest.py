def solution(players, callings):
    answer = []
    
    position = {name: idx for idx, name in enumerate(players)}
    
    for palyer in callings:
        rank = position[palyer]
        players[rank - 1], players[rank] = players[rank], players[rank - 1]
        answer = players
        print(answer)
    return answer



players = ["mumu", "soe", "poe", "kai", "mine"]
callings = ["kai", "kai", "mine", "mine"]
 
result = solution(players, callings)