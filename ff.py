import heapq

def dijkstra(graph, start):
    distances = {vertex: float('inf') for vertex in graph}
    distances[start] = 0
    
    priority_queue = [(0, start)]  
    
    predecessors = {vertex: None for vertex in graph}
    
    while priority_queue:
        current_distance, current_vertex = heapq.heappop(priority_queue)
        
        if current_distance > distances[current_vertex]:
            continue
        
        for neighbor, weight in graph[current_vertex].items():
            distance = current_distance + weight
            
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                predecessors[neighbor] = current_vertex
                heapq.heappush(priority_queue, (distance, neighbor))
    
    return distances, predecessors

def reconstruct_path(predecessors, start, end):
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = predecessors[current]
    
    path.reverse()
    return path if path[0] == start else []


graph = {
    'A': {'B': 2, 'C': 3, 'D': 4},
    'B': {'E': 7},
    'C': {'E': 5, 'G': 9, 'F': 3, 'D': 1},
    'D': {'F': 5},
    'E': {'G': 4},
    'F': {'G': 4},
    'G': {}
}

start_vertex = 'A'
end_vertex = 'G'

# Получаем расстояния и предшественников
distances, predecessors = dijkstra(graph, start_vertex)

# Восстанавливаем кратчайший путь
path = reconstruct_path(predecessors, start_vertex, end_vertex)

print(f"Кратчайшее расстояние от {start_vertex} до {end_vertex}: {distances[end_vertex]}")
print(f"Путь: {' -> '.join(path)}")
