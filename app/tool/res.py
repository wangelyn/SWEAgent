from functools import cache
def resolution(matrix):
    n , m = len(matrix) , len(matrix[0])
    @cache
    def dfs(i , j) :
        if i < 0 or j < 0 or i >= n or j >= m or matrix[i][j] == 2 :
            return inf
        if matrix[i][j] == 0:
            return 0
        matrix[i][j] == 2
        return min(dfs(i - 1 , j) + 1 , dfs(i + 1,j) + 1, dfs(i ,j + 1) +  1 , dfs(i , j - 1) + 1)

    ma = [[0] * n] * m

    for i in range(n) :
        for j in range(m) :
            ma[i][j] = dfs(i , j)

    return ma

input = [[0,0,0] , [0,1,0],[0,0,0]]
print(resolution(input))
