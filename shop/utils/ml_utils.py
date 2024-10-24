import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..models import Order, Product
import random

class RecommendationSystem:
    def __init__(self):
        try:
            self.product_popularity = joblib.load('product_popularity.joblib')
            self.vectorizer = joblib.load('vectorizer.joblib')
            self.cosine_sim = joblib.load('cosine_sim.joblib')
        except FileNotFoundError:
            print("Model files not found. Initializing with empty data.")
            self.product_popularity = pd.DataFrame(columns=['Product', 'Quantity', 'PopularityScore'])
            self.vectorizer = TfidfVectorizer()
            self.cosine_sim = None

    def update_model(self, new_orders):
        if not new_orders:
            print("No new orders to process.")
            return

        # Convert new orders to DataFrame
        new_df = pd.DataFrame(new_orders)
        
        # Update product popularity
        new_popularity = new_df.groupby('product_name')['quantity'].sum().reset_index()
        new_popularity.columns = ['Product', 'Quantity']
        
        self.product_popularity = pd.concat([self.product_popularity, new_popularity]).groupby('Product')['Quantity'].sum().reset_index()
        
        # Calculate relative popularity score (1-100 scale)
        max_quantity = self.product_popularity['Quantity'].max()
        min_quantity = self.product_popularity['Quantity'].min()
        
        if max_quantity == min_quantity:
            self.product_popularity['PopularityScore'] = 100
        else:
            self.product_popularity['PopularityScore'] = ((self.product_popularity['Quantity'] - min_quantity) / (max_quantity - min_quantity) * 99 + 1).round().astype(int)
        
        # Update TF-IDF matrix and cosine similarity
        if len(self.product_popularity) > 1:
            tfidf_matrix = self.vectorizer.fit_transform(self.product_popularity['Product'])
            self.cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        else:
            print("Not enough data to compute cosine similarity.")
            self.cosine_sim = None
        
        # Save updated model
        joblib.dump(self.product_popularity, 'product_popularity.joblib')
        joblib.dump(self.vectorizer, 'vectorizer.joblib')
        if self.cosine_sim is not None:
            joblib.dump(self.cosine_sim, 'cosine_sim.joblib')

    def get_recommendations(self, product_name, n=5):
        if self.cosine_sim is None or len(self.product_popularity) < 2:
            print("Not enough data for recommendations.")
            return []

        # Get index of the product
        if product_name not in self.product_popularity['Product'].values:
            print(f"Product '{product_name}' not found in the data.")
            return []

        idx = self.product_popularity[self.product_popularity['Product'] == product_name].index[0]
        
        # Get similarity scores
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:n+1]  # Exclude the product itself
        
        # Get product indices
        product_indices = [i[0] for i in sim_scores]
        
        # Return recommended products with their popularity scores
        recommendations = self.product_popularity.iloc[product_indices]
        return recommendations[['Product', 'PopularityScore']].to_dict('records')

recommendation_system = RecommendationSystem()

def get_product_recommendations(shop_id, offset=0, limit=12):
    current_shop_products = Product.objects.filter(shop_id=shop_id).values_list('product_name', flat=True)
    all_products = recommendation_system.product_popularity['Product'].tolist()
    products_to_recommend = list(set(all_products) - set(current_shop_products))
    
    if not products_to_recommend:
        return []
    
    recommendations = []
    for product in products_to_recommend:
        recommendations.extend(recommendation_system.get_recommendations(product))
    
    # Remove duplicates and sort by popularity
    unique_recommendations = []
    seen = set()
    for r in recommendations:
        if r['Product'] not in seen and r['Product'] not in current_shop_products:
            unique_recommendations.append(r)
            seen.add(r['Product'])
    
    unique_recommendations.sort(key=lambda x: x['PopularityScore'], reverse=True)
    return unique_recommendations[offset:offset+limit]

def update_model_with_new_orders():
    # Fetch new orders since last update
    last_update = Order.objects.latest('order_date').order_date if Order.objects.exists() else None
    new_orders = Order.objects.filter(order_date__gt=last_update) if last_update else Order.objects.all()
    
    print("Debug: Number of new orders:", new_orders.count())
    
    # Prepare data for model update
    order_data = []
    for order in new_orders:
        for order_detail in order.order_details.all():
            order_data.append({
                'product_name': order_detail.product.product_name,
                'quantity': order_detail.quantity
            })
    
    print("Debug: order_data:", order_data)
    
    # Update the model
    recommendation_system.update_model(order_data)

# Initialize the model with existing data
def initialize_model():
    from shop.models import Order  # Move this import inside the function
    all_orders = Order.objects.all()
    order_data = []
    for order in all_orders:
        for order_detail in order.order_details.all():
            order_data.append({
                'product_name': order_detail.product.product_name,
                'quantity': order_detail.quantity
            })
    recommendation_system.update_model(order_data)

# Call this function when the server starts
# initialize_model()  # Remove or comment out this line
