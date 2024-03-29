import networkx as nx
import random
from pyvis.network import Network
import webbrowser

# Neo4j connection parameters
uri = "bolt://localhost:7689"
user = "neo4j"
password = "abcd1234"

# Define product categories and their similarities
categories = {
    "Electronics": ["Laptop", "Smartphone", "Headphones", "Smartwatch", "Gaming Console"],
    "Clothing": ["T-Shirt", "Jeans", "Dress", "Jacket", "Shoes"],
    "Home Appliances": ["Refrigerator", "Washing Machine", "Microwave", "Vacuum Cleaner", "Air Conditioner"],
    "Sports": ["Basketball", "Tennis Racket", "Yoga Mat", "Weights", "Running Shoes"],
    "Books": ["Fiction Novel", "Cookbook", "Biography", "Self-Help Book", "Children's Book"]
}

# Define additional "must-buy" products for each category
must_buy = {
    "Electronics": ["Laptop Bag", "Laptop Cooler", "Laptop Insurance", "Wireless Mouse", "External Hard Drive"],
    "Clothing": ["Belt", "Socks", "Underwear", "Wallet", "Scarf"],
    "Home Appliances": ["Appliance Insurance", "Appliance Extended Warranty", "Cleaning Supplies", "Repair Kit", "Spare Parts"],
    "Sports": ["Water Bottle", "Gym Bag", "Sweatbands", "Sports Towel", "Sports Nutrition"],
    "Books": ["Bookmarks", "Book Light", "Book Organizer", "Book Stand", "Book Sleeve"]
}

# Define the product graph
G = nx.Graph()

# Add product nodes and edges based on categories
for category, products in categories.items():
    for product1 in products:
        G.add_node(product1, node_type="Product", category=category)
        for product2 in products:
            if product1 != product2:
                similarity = random.uniform(0.6, 0.9)  # Higher similarity within the same category
                G.add_edge(product1, product2, weight=similarity)

        # Add "must-buy" products and assign higher similarity scores
        for must_buy_product in must_buy[category]:
            G.add_node(must_buy_product, node_type="Must-Buy", category=category)
            similarity = random.uniform(0.8, 0.95)  # Higher similarity between main product and "must-buy"
            G.add_edge(product1, must_buy_product, weight=similarity)

    # Add edges between products in different categories with lower similarity
    for other_category, other_products in categories.items():
        if other_category != category:
            for product1 in products:
                for product2 in other_products:
                    similarity = random.uniform(0.2, 0.5)  # Lower similarity across categories
                    G.add_edge(product1, product2, weight=similarity)

# Visualize the graph with PyVis
net = Network(height='750px', width='100%', bgcolor='#F5F5F5', font_color='black')
net.barnes_hut(gravity=-80000, central_gravity=0.3, spring_length=100, spring_strength=0.001)

# Set node properties
node_color_map = {
    'Electronics': 'blue',
    'Clothing': 'green',
    'Home Appliances': 'orange',
    'Sports': 'red',
    'Books': 'purple'
}

node_shape_map = {
    'Product': 'circle',
    'Must-Buy': 'square'
}

node_size_map = {
    'Product': 30,
    'Must-Buy': 25
}

default_color = 'gray'
default_shape = 'circle'
default_size = 25

for node in G.nodes:
    node_category = G.nodes[node]['category']
    node_color = node_color_map.get(node_category, default_color)
    node_shape = node_shape_map.get(G.nodes[node]['node_type'], default_shape)
    node_size = node_size_map.get(G.nodes[node]['node_type'], default_size)
    net.add_node(node, label=node, color=node_color, shape=node_shape, size=node_size)

# Add edges
for edge in G.edges(data=True):
    source, target, attrs = edge
    weight = attrs['weight']
    net.add_edge(source, target, label=str(round(weight, 2)))

# Define a function to find similar products using KNN
def find_similar_products(G, target_product, k):
    neighbors = sorted(list(G[target_product].items()), key=lambda x: x[1]['weight'], reverse=True)[:k]
    return [(neighbor[0], neighbor[1]['weight']) for neighbor in neighbors]

# Find similar products for a given product
target_product = "Laptop"
k = 5
similar_products = find_similar_products(G, target_product, k)
print(f"Similar products to '{target_product}':")
for product, similarity in similar_products:
    print(f"{product} (similarity: {similarity:.2f})")

# Save the graph to an HTML file
graph_html_file = 'product_similarity_graph.html'
net.save_graph(graph_html_file)
print(f"Graph exported to '{graph_html_file}'")

# Open the HTML file in a web browser
webbrowser.open_new_tab(graph_html_file)




from neo4j import GraphDatabase

def networkx_to_neo4j(G, uri, user, password):
    try:
        # Create a Neo4j driver instance
        driver = GraphDatabase.driver(uri, auth=(user, password))

        # Create a session
        with driver.session() as session:
            # Clear the existing nodes and relationships in Neo4j
            session.run("MATCH (n) DETACH DELETE n")

            # Create nodes in Neo4j
            for node in G.nodes:
                node_type = G.nodes[node]['node_type']
                node_label = node_type.capitalize()
                node_category = G.nodes[node]['category']
                query = "CREATE (n:`{node_label}` {name: $name, category: $category})"
                session.run(query, name=node, category=node_category)

            # Create relationships in Neo4j
            for source, target, edge_data in G.edges(data=True):
                weight = edge_data['weight']
                query = "MATCH (a), (b) WHERE a.name = $source AND b.name = $target MERGE (a)-[r:SIMILAR {weight: $weight}]->(b)"
                session.run(query, source=source, target=target, weight=weight)

        print("Successfully imported graph into Neo4j!")

    except Exception as e:
        print(f"Error occurred while importing graph into Neo4j: {e}")

    finally:
        # Close the driver
        if driver:
            driver.close()


def main():
    # Call the function to convert the NetworkX graph to Neo4j
    networkx_to_neo4j(G, uri, user, password)


if __name__ == "__main__":
    main()