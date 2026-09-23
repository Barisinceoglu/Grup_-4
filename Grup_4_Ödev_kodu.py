import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
import uuid # Benzersiz kimlikler oluşturmak için
from enum import Enum # Sipariş durumları için Enum kullanmak için

# --- 1. Veri Dosyaları Kurulumu ---
# Ürün ve müşteri verileri için dosya yollarını tanımla
PRODUCTS_FILE = "products.json"
CUSTOMERS_FILE = "customers.json"
ORDERS_FILE = "orders.json" # Siparişler için de dosya tanımla

# --- 2. Temel Sınıflar ---

class OrderStatus(Enum):
    """Siparişin olası durumlarını temsil eden bir Enum."""
    PENDING = "Beklemede"
    PROCESSING = "İşleniyor"
    SHIPPED = "Gönderildi"
    DELIVERED = "Teslim Edildi"
    CANCELLED = "İptal Edildi"

    def __str__(self):
        return self.value

class Product:
    """
    Sistemdeki bir ürünü temsil eder.
    Nitelikler:
        product_id (str): Ürün için benzersiz tanımlayıcı.
        name (str): Ürünün adı.
        price (float): Ürünün fiyatı.
        stock (int): Mevcut stok miktarı.
        category (str): Ürünün kategorisi (örn: Elektronik, Giyim).
    """
    def __init__(self, product_id, name, price, stock, category):
        self.product_id = str(product_id)
        self.name = name
        self.price = float(price)
        self.stock = int(stock)
        self.category = category

    def display_info(self):
        """Ürünün detaylarını konsola yazdırır."""
        print(f"  ID: {self.product_id}, Ad: {self.name}, Fiyat: ${self.price:.2f}, Stok: {self.stock}, Kategori: {self.category}")

    def update_stock(self, quantity_change):
        """
        Ürünün stok miktarını günceller.
        Argümanlar:
            quantity_change (int): Stoğu değiştirecek miktar.
                                   Ekleme için pozitif, çıkarma için negatif.
        Dönüş:
            bool: Stok başarıyla güncellendiyse True, aksi takdirde False (örn: yetersiz stok).
        """
        if self.stock + quantity_change < 0:
            print(f"Hata: '{self.name}' için yeterli stok yok. Mevcut: {self.stock}")
            return False
        self.stock += quantity_change
        return True

    def to_dict(self):
        """Product nesnesini JSON serileştirme için bir sözlüğe dönüştürür."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "category": self.category
        }

    @staticmethod
    def from_dict(data):
        """Bir sözlükten (örn: JSON'dan yüklenen) bir Product nesnesi oluşturur."""
        return Product(data["product_id"], data["name"], data["price"], data["stock"], data["category"])


class Customer:
    """
    Sistemdeki bir müşteriyi temsil eder.
    Nitelikler:
        customer_id (str): Müşteri için benzersiz tanımlayıcı.
        name (str): Müşterinin adı.
        email (str): Müşterinin e-posta adresi.
        address (str): Müşterinin gönderim adresi.
        order_history (list): Bu müşteriyle ilişkili sipariş kimliklerini saklamak için bir liste.
    """
    def __init__(self, customer_id, name, email, address, order_history=None):
        self.customer_id = str(customer_id)
        self.name = name
        self.email = email
        self.address = address
        self.order_history = order_history if order_history is not None else []

    def display_profile(self):
        """Müşterinin profil detaylarını yazdırır."""
        print(f"  Müşteri ID: {self.customer_id}")
        print(f"  Ad: {self.name}")
        print(f"  E-posta: {self.email}")
        print(f"  Adres: {self.address}")
        print(f"  Sipariş Sayısı: {len(self.order_history)}")

    def add_order_to_history(self, order_id):
        """Bir sipariş kimliğini müşterinin sipariş geçmişine ekler."""
        if order_id not in self.order_history:
            self.order_history.append(order_id)

    def to_dict(self):
        """Customer nesnesini JSON serileştirme için bir sözlüğe dönüştürür."""
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "address": self.address,
            "order_history": self.order_history
        }

    @staticmethod
    def from_dict(data):
        """Bir sözlükten (örn: JSON'dan yüklenen) bir Customer nesnesi oluşturur."""
        return Customer(data["customer_id"], data["name"], data["email"], data["address"], data.get("order_history", []))


class Order:
    """
    Bir müşteri tarafından verilen bir siparişi temsil eder.
    Nitelikler:
        order_id (str): Sipariş için benzersiz tanımlayıcı.
        customer_id (str): Siparişi veren müşterinin ID'si.
        products (dict): Anahtarların ürün ID'leri, değerlerin ise miktarlar olduğu bir sözlük.
        order_date (str): Siparişin verildiği tarih ve saat (ISO formatında).
        status (OrderStatus): Siparişin mevcut durumu (Enum değeri).
        shipping_method_name (str): Seçilen gönderim yönteminin adı (örn: 'Hızlı Gönderim').
        shipping_cost (float): Hesaplanan gönderim maliyeti.
        total_amount (float): Ürünlerin toplam maliyeti + gönderim.
    """
    def __init__(self, order_id, customer_id, products, order_date, status: OrderStatus, shipping_method_name, shipping_cost, total_amount):
        self.order_id = str(order_id)
        self.customer_id = str(customer_id)
        self.products = products  # {product_id: quantity}
        self.order_date = order_date
        self.status = status # Artık OrderStatus Enum üyesi
        self.shipping_method_name = shipping_method_name
        self.shipping_cost = float(shipping_cost)
        self.total_amount = float(total_amount)

    def display_order_details(self, inventory_manager):
        """
        Siparişin detaylarını, ürün adları dahil olmak üzere yazdırır.
        Argümanlar:
            inventory_manager (InventoryManager): Ürün detaylarını almak için yönetici.
        """
        print(f"\n--- Sipariş Detayları (ID: {self.order_id}) ---")
        print(f"  Müşteri ID: {self.customer_id}")
        print(f"  Sipariş Tarihi: {self.order_date}")
        print(f"  Durum: {self.status.value}") # Enum'ın değerini göster
        print(f"  Gönderim Yöntemi: {self.shipping_method_name} (${self.shipping_cost:.2f})")
        print("  Ürünler:")
        for prod_id, qty in self.products.items():
            product = inventory_manager.get_product(prod_id)
            if product:
                print(f"    - {product.name} (ID: {prod_id}) x {qty} @ ${product.price:.2f} her biri")
            else:
                print(f"    - Bilinmeyen Ürün (ID: {prod_id}) x {qty}")
        print(f"  Toplam Tutar: ${self.total_amount:.2f}")
        print("------------------------------------")

    def update_status(self, new_status: OrderStatus):
        """
        Sipariş durumunu günceller.
        Argümanlar:
            new_status (OrderStatus): Sipariş için yeni durum (Enum değeri).
        """
        self.status = new_status
        print(f"Sipariş {self.order_id} durumu şuna güncellendi: {self.status.value}")
        # Gerçek bir sistemde, bu doğrudan NotificationService'i tetiklerdi.

    def cancel_order(self, inventory_manager):
        """
        Siparişin durumunu 'İptal Edildi' olarak ayarlar ve stokları geri alır.
        Argümanlar:
            inventory_manager (InventoryManager): Stokları güncellemek için yönetici.
        Dönüş:
            bool: İptal başarılıysa True, aksi takdirde False.
        """
        if self.status == OrderStatus.CANCELLED:
            print(f"Sipariş {self.order_id} zaten iptal edilmiş.")
            return False
        
        if self.status in [OrderStatus.DELIVERED, OrderStatus.SHIPPED]: # İptal edilemeyecek durumlar
            print(f"Sipariş {self.order_id} {self.status.value} durumunda olduğu için iptal edilemez.")
            return False

        # Stokları geri al
        print(f"Sipariş {self.order_id} için stoklar geri alınıyor...")
        for prod_id, qty in self.products.items():
            success = inventory_manager.update_stock(prod_id, qty) # Stoğu artır
            if not success:
                print(f"Uyarı: Ürün ID {prod_id} için stok geri alırken sorun oluştu. Manuel kontrol gerekebilir.")
                # Bu durumda iptali durdurmak veya devam etmek stratejiye bağlıdır.
                # Şimdilik devam ediyoruz ancak uyarı veriyoruz.
        
        self.status = OrderStatus.CANCELLED
        print(f"Sipariş {self.order_id} iptal edildi ve stoklar geri alındı.")
        return True


    def to_dict(self):
        """Order nesnesini JSON serileştirme için bir sözlüğe dönüştürür."""
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "products": self.products,
            "order_date": self.order_date,
            "status": self.status.value, # Enum değerini string olarak kaydet
            "shipping_method_name": self.shipping_method_name,
            "shipping_cost": self.shipping_cost,
            "total_amount": self.total_amount
        }

    @staticmethod
    def from_dict(data):
        """Bir sözlükten (örn: JSON'dan yüklenen) bir Order nesnesi oluşturur."""
        # JSON'dan okurken string değeri Enum üyesine dönüştür
        status_enum = None
        for s in OrderStatus:
            if s.value == data["status"]:
                status_enum = s
                break
        if status_enum is None:
            # Varsayılan bir durum veya hata işleme
            status_enum = OrderStatus.PENDING 
            print(f"Uyarı: Bilinmeyen sipariş durumu '{data['status']}' için varsayılan 'Beklemede' kullanıldı.")

        return Order(
            data["order_id"],
            data["customer_id"],
            data["products"],
            data["order_date"],
            status_enum, # Enum üyesi olarak ata
            data["shipping_method_name"],
            data["shipping_cost"],
            data["total_amount"]
        )


# --- 3. Tasarım Desenleri Uygulaması ---

# Strateji Deseni: Gönderim Yöntemleri
class ShippingMethod(ABC):
    """Farklı gönderim stratejileri için soyut temel sınıf."""
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def calculate_cost(self, distance, total_weight=0, total_volume=0):
        """
        Çeşitli faktörlere göre gönderim maliyetini hesaplar.
        Argümanlar:
            distance (float): Hedefe olan mesafe.
            total_weight (float): Siparişin toplam ağırlığı.
            total_volume (float): Siparişin toplam hacmi.
        Dönüş:
            float: Hesaplanan gönderim maliyeti.
        """
        pass

class FastShipping(ShippingMethod):
    """Hızlı gönderim için somut strateji."""
    def __init__(self):
        super().__init__("Hızlı Gönderim")

    def calculate_cost(self, distance, total_weight=0, total_volume=0):
        # Örnek: Daha yüksek temel maliyet, orta düzeyde km başına
        return 15.0 + (distance * 0.75) + (total_weight * 0.5)

class EconomicShipping(ShippingMethod):
    """Ekonomik gönderim için somut strateji."""
    def __init__(self):
        super().__init__("Ekonomik Gönderim")

    def calculate_cost(self, distance, total_weight=0, total_volume=0):
        # Örnek: Daha düşük temel maliyet, daha düşük km başına
        return 5.0 + (distance * 0.25) + (total_weight * 0.1)

class DroneShipping(ShippingMethod):
    """Drone gönderimi için somut strateji (mesafe sınırlamaları olabilir)."""
    def __init__(self):
        super().__init__("Drone Gönderim")

    def calculate_cost(self, distance, total_weight=0, total_volume=0):
        # Örnek: Yüksek temel maliyet, ancak kısa mesafeler için çok verimli
        if distance > 101: # Drone'un maksimum menzili olabilir
            print("Drone gönderimi bu mesafe için mevcut değil.")
            return float('inf') # Mevcut olmadığını belirtir
        return 25.0 + (distance * 0.1) + (total_weight * 1.0) # Drone'lar ağırlığa duyarlı olabilir


# Gözlemci Deseni: Bildirim Servisi
class NotificationService:
    """
    Hem Konu hem de Gözlemci olarak görev yapan basit bir bildirim hizmeti.
    Sipariş durumu değişikliklerini gözlemler ve müşterileri bilgilendirir.
    """
    def __init__(self):
        self._observers = {} # {customer_id: Customer_object}

    def attach(self, customer):
        """Bir müşteriyi bildirim almak üzere ekler."""
        self._observers[customer.customer_id] = customer
        print(f"Bildirim Servisi: Müşteri {customer.name} eklendi.")

    def detach(self, customer_id):
        """Bir müşteriyi bildirim almaktan kaldırır."""
        if customer_id in self._observers:
            del self._observers[customer_id]
            print(f"Bildirim Servisi: Müşteri {customer_id} kaldırıldı.")

    def notify(self, customer_id, message):
        """Belirli bir müşteriyi bilgilendirir."""
        customer = self._observers.get(customer_id)
        if customer:
            print(f"\n--- {customer.name} ({customer.email}) için Bildirim ---")
            print(f"  Mesaj: {message}")
            print("------------------------------------------")
        else:
            print(f"Bildirim Servisi: Bildirim için müşteri {customer_id} bulunamadı.")


# Singleton Deseni: Envanter Yöneticisi
class InventoryManager:
    """
    Tüm ürün envanterini yönetir. Ürün verilerini ve stok seviyelerini
    tek bir örneğin kontrol etmesini sağlamak için Singleton olarak uygulanmıştır.
    """
    _instance = None
    _products = {} # {product_id: Product_object}

    def __new__(cls):
        """InventoryManager'ın yalnızca bir örneğinin oluşturulmasını sağlar."""
        if cls._instance is None:
            cls._instance = super(InventoryManager, cls).__new__(cls)
            # Ürünleri burada başlat (ilk oluşturma sırasında)
            cls._instance._products = {}
            cls._instance.load_products() # İlk örnekleme sırasında ürünleri yükle
        return cls._instance

    def load_products(self):
        """Ürün verilerini PRODUCTS_FILE'dan (JSON) yükler."""
        if os.path.exists(PRODUCTS_FILE):
            try:
                with open(PRODUCTS_FILE, 'r') as f:
                    products_data = json.load(f)
                    for prod_data in products_data:
                        product = Product.from_dict(prod_data)
                        self._products[product.product_id] = product
                print(f"{len(self._products)} ürün {PRODUCTS_FILE} dosyasından yüklendi.")
            except json.JSONDecodeError:
                print(f"{PRODUCTS_FILE} okunurken hata oluştu. Boş envanterle başlatılıyor.")
                self._products = {}
        else:
            print(f"{PRODUCTS_FILE} bulunamadı. Boş envanterle başlatılıyor.")
            # İsteğe bağlı olarak, dosya yoksa bazı varsayılan ürünler ekle
            self._products = {
                "1": Product("1", "Dizüstü Bilgisayar", 1200.0, 50, "Elektronik"),
                "2": Product("2", "Fare", 25.0, 100, "Elektronik"),
                "3": Product("3", "Klavye", 75.0, 75, "Elektronik"),
                "4": Product("4", "Tişört", 20.0, 200, "Giyim"),
                "5": Product("5", "Kot Pantolon", 50.0, 150, "Giyim"),
            }
            self.save_products() # Varsayılan ürünleri kaydet
            print("Varsayılan ürünler oluşturuldu ve kaydedildi.")


    def save_products(self):
        """Mevcut ürün verilerini PRODUCTS_FILE'a (JSON) kaydeder."""
        products_data = [p.to_dict() for p in self._products.values()]
        with open(PRODUCTS_FILE, 'w') as f:
            json.dump(products_data, f, indent=4)
        print(f"{len(self._products)} ürün {PRODUCTS_FILE} dosyasına kaydedildi.")

    def get_product(self, product_id):
        """Ürün ID'sine göre bir Product nesnesi alır."""
        return self._products.get(str(product_id))

    def list_products(self, category=None):
        """
        Tüm ürünleri listeler, isteğe bağlı olarak kategoriye göre filtreler.
        Argümanlar:
            category (str, optional): Ürünleri bu kategoriye göre filtrele.
        Dönüş:
            list: Product nesnelerinin bir listesi.
        """
        if category:
            return [p for p in self._products.values() if p.category.lower() == category.lower()]
        return list(self._products.values())

    def check_stock(self, product_id, quantity):
        """Bir ürünün yeterli stoğu olup olmadığını kontrol eder."""
        product = self.get_product(product_id)
        return product and product.stock >= quantity

    def update_stock(self, product_id, quantity_change):
        """Belirli bir ürünün stoğunu günceller."""
        product = self.get_product(product_id)
        if product:
            return product.update_stock(quantity_change)
        return False

    def add_product(self, product):
        """Yeni bir ürünü envantere ekler."""
        if product.product_id in self._products:
            print(f"Hata: ID {product.product_id} zaten mevcut.")
            return False
        self._products[product.product_id] = product
        self.save_products()
        return True


# Fabrika Metodu Deseni: Sipariş Fabrikası
class OrderFactory:
    """
    Order nesneleri oluşturmaktan sorumlu bir fabrika sınıfı.
    Bu desen, esnek sipariş oluşturma mantığına izin verir.
    """
    @staticmethod
    def create_order(customer_id, products_in_cart, shipping_method, inventory_manager):
        """
        Yeni bir Order nesnesi oluşturur.
        Argümanlar:
            customer_id (str): Siparişi veren müşterinin ID'si.
            products_in_cart (dict): {ürün_id: miktar} sözlüğü.
            shipping_method (ShippingMethod): Seçilen gönderim stratejisi nesnesi.
            inventory_manager (InventoryManager): Envanter yöneticisi örneği.
        Dönüş:
            Order veya None: Başarılı olursa oluşturulan Order nesnesi, aksi takdirde None.
        """
        order_id = str(uuid.uuid4()) # Benzersiz bir sipariş ID'si oluştur
        order_date = datetime.now().isoformat()
        status = OrderStatus.PENDING # Başlangıç durumu Enum olarak
        total_products_cost = 0.0
        total_weight = 0.0 # Ağırlık hesaplaması için yer tutucu
        total_volume = 0.0 # Hacim hesaplaması için yer tutucu

        # İlk olarak, tüm stoğu işlemeden önce kontrol et
        for prod_id, qty in products_in_cart.items():
            product = inventory_manager.get_product(prod_id)
            if not product or not inventory_manager.check_stock(prod_id, qty):
                print(f"Sipariş oluşturma başarısız: Ürün ID {prod_id} için yetersiz stok.")
                return None
            total_products_cost += product.price * qty
            # Basitlik için ağırlık/hacim varsayımı, veya Product sınıfına ekle
            total_weight += qty * 0.1 # Örnek: öğe başına 0.1 kg
            total_volume += qty * 0.01 # Örnek: öğe başına 0.01 metreküp

        # Seçilen stratejiyi kullanarak gönderim maliyetini hesapla
        # Basitlik için, şimdilik sabit bir mesafe varsay, veya kullanıcıdan iste
        distance = 100 # Örnek mesafe km cinsinden
        shipping_cost = shipping_method.calculate_cost(distance, total_weight, total_volume)

        if shipping_cost == float('inf'): # Gönderim yöntemi mevcut olmadığını belirtti
            print("Sipariş oluşturma başarısız: Seçilen gönderim yöntemi bu sipariş için mevcut değil.")
            return None

        total_amount = total_products_cost + shipping_cost

        # Tüm kontroller geçerse, stoğu güncelle ve siparişi oluştur
        for prod_id, qty in products_in_cart.items():
            inventory_manager.update_stock(prod_id, -qty) # Stoğu azalt

        return Order(order_id, customer_id, products_in_cart, order_date, status,
                     shipping_method.name, shipping_cost, total_amount)


# --- 4. Ana Uygulama Mantığı ve Fonksiyonel CLI ---

# Global olarak erişilebilecek sistem bileşenleri
inventory_manager = InventoryManager() # Singleton örneği
notification_service = NotificationService()
customers = {} # {customer_id: Customer_object}
orders = {} # {order_id: Order_object}
current_customer = None # Oturum açmış bir kullanıcıyı simüle etmek için

def _load_customers():
    """Müşteri verilerini CUSTOMERS_FILE'dan (JSON) yükler."""
    global customers, notification_service
    if os.path.exists(CUSTOMERS_FILE):
        try:
            with open(CUSTOMERS_FILE, 'r') as f:
                customers_data = json.load(f)
                for cust_data in customers_data:
                    customer = Customer.from_dict(cust_data)
                    customers[customer.customer_id] = customer
            print(f"{len(customers)} müşteri {CUSTOMERS_FILE} dosyasından yüklendi.")
        except json.JSONDecodeError:
            print(f"{CUSTOMERS_FILE} okunurken hata oluştu. Müşteri olmadan başlatılıyor.")
            customers = {}
    else:
        print(f"{CUSTOMERS_FILE} bulunamadı. Müşteri olmadan başlatılıyor.")
        # İsteğe bağlı olarak, varsayılan bir müşteri ekle
        default_customer = Customer("101", "Ayşe Yılmaz", "ayse@example.com", "123 Ana Cadde, Herhangi Bir Şehir")
        customers[default_customer.customer_id] = default_customer
        _save_customers()
        print("Varsayılan müşteri oluşturuldu ve kaydedildi.")
    
    # Tüm mevcut müşterileri bildirim hizmetine ekle
    for customer in customers.values():
        notification_service.attach(customer)

def _save_customers():
    """Mevcut müşteri verilerini CUSTOMERS_FILE'a (JSON) kaydeder."""
    customers_data = [c.to_dict() for c in customers.values()]
    with open(CUSTOMERS_FILE, 'w') as f:
        json.dump(customers_data, f, indent=4)
    print(f"{len(customers)} müşteri {CUSTOMERS_FILE} dosyasına kaydedildi.")

def _load_orders():
    """Sipariş verilerini bir JSON dosyasından (örn: orders.json) yükler."""
    global orders
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, 'r') as f:
                orders_data = json.load(f)
                for order_data in orders_data:
                    order = Order.from_dict(order_data)
                    orders[order.order_id] = order
            print(f"{len(orders)} sipariş {ORDERS_FILE} dosyasından yüklendi.")
        except json.JSONDecodeError:
            print(f"{ORDERS_FILE} okunurken hata oluştu. Sipariş olmadan başlatılıyor.")
            orders = {}
    else:
        print(f"{ORDERS_FILE} bulunamadı. Sipariş olmadan başlatılıyor.")

def _save_orders():
    """Mevcut sipariş verilerini bir JSON dosyasına (örn: orders.json) kaydeder."""
    orders_data = [o.to_dict() for o in orders.values()]
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders_data, f, indent=4)
    print(f"{len(orders)} sipariş {ORDERS_FILE} dosyasına kaydedildi.")

def register_customer():
    """Yeni bir müşterinin kaydolmasına izin verir."""
    global current_customer, customers, notification_service
    print("\n--- Yeni Müşteri Kaydı ---")
    customer_id = str(uuid.uuid4())[:8] # Görüntüleme için kısa benzersiz ID
    name = input("Adınızı girin: ")
    email = input("E-posta adresinizi girin: ")
    address = input("Adresinizi girin: ")

    new_customer = Customer(customer_id, name, email, address)
    customers[customer_id] = new_customer
    _save_customers()
    notification_service.attach(new_customer) # Yeni müşteriyi bildirimler için ekle
    print(f"Müşteri '{name}' başarıyla kaydedildi. ID: {customer_id}")
    current_customer = new_customer
    print(f"{new_customer.name} olarak otomatik giriş yapıldı.")

def login_customer():
    """Mevcut bir müşterinin giriş yapmasına izin verir."""
    global current_customer, customers
    print("\n--- Müşteri Girişi ---")
    customer_id = input("Müşteri ID'nizi girin: ")
    customer = customers.get(customer_id)
    if customer:
        current_customer = customer
        print(f"{customer.name} olarak giriş yapıldı.")
    else:
        print("Geçersiz Müşteri ID'si. Lütfen tekrar deneyin veya kaydolun.")

def logout_customer():
    """Mevcut müşterinin çıkış yapmasına izin verir."""
    global current_customer
    if current_customer:
        print(f"{current_customer.name} hesabından çıkış yapıldı.")
        current_customer = None
    else:
        print("Şu anda giriş yapmış bir müşteri yok.")

def browse_products():
    """Mevcut ürünleri, isteğe bağlı kategori filtrelemesi ile görüntüler."""
    print("\n--- Mevcut Ürünler ---")
    category = input("Filtrelemek için kategori girin (tümü için boş bırakın): ").strip()
    products_to_display = inventory_manager.list_products(category)

    if not products_to_display:
        print("Bu kategori için ürün bulunamadı." if category else "Hiç ürün mevcut değil.")
        return

    for product in products_to_display:
        product.display_info()
    print("--------------------------")

def place_order():
    """Müşteriyi yeni bir sipariş verme sürecinde yönlendirir."""
    global current_customer, orders, inventory_manager, notification_service
    if not current_customer:
        print("Sipariş vermek için lütfen giriş yapın veya kaydolun.")
        return

    print(f"\n--- {current_customer.name} için Yeni Sipariş Ver ---")
    cart = {}
    while True:
        browse_products() # Ürünleri göster
        product_id = input("Sepete eklemek için Ürün ID'sini girin (veya 'bitir' yazıp çıkın): ").strip()
        if product_id.lower() == 'bitir':
            break

        product = inventory_manager.get_product(product_id)
        if not product:
            print("Geçersiz Ürün ID'si. Lütfen tekrar deneyin.")
            continue

        try:
            quantity = int(input(f"{product.name} için miktar girin: "))
            if quantity <= 0:
                print("Miktar pozitif olmalıdır.")
                continue
        except ValueError:
            print("Geçersiz miktar. Lütfen bir sayı girin.")
            continue

        if not inventory_manager.check_stock(product_id, quantity):
            print(f"{product.name} için yeterli stok yok. Mevcut: {product.stock}")
            continue

        cart[product_id] = cart.get(product_id, 0) + quantity
        print(f"Sepete {quantity} x {product.name} eklendi. Mevcut sepet: {cart}")

    if not cart:
        print("Sepet boş. Sipariş iptal edildi.")
        return

    print("\n--- Gönderim Yöntemi Seçin ---")
    shipping_options = {
        "1": FastShipping(),
        "2": EconomicShipping(),
        "3": DroneShipping()
    }
    for key, method in shipping_options.items():
        # Gösterim için, sahte bir mesafe ile maliyeti hesapla
        dummy_cost = method.calculate_cost(100)
        print(f"  {key}. {method.name} (Tahmini Maliyet: ${dummy_cost:.2f})")

    selected_shipping_method = None
    while selected_shipping_method is None:
        choice = input("Seçiminizi girin (1-3): ").strip()
        selected_shipping_method = shipping_options.get(choice)
        if not selected_shipping_method:
            print("Geçersiz seçim. Lütfen 1, 2 veya 3 girin.")

    # Fabrika Metodu kullanarak siparişi oluştur
    new_order = OrderFactory.create_order(
        current_customer.customer_id,
        cart,
        selected_shipping_method,
        inventory_manager
    )

    if new_order:
        orders[new_order.order_id] = new_order
        current_customer.add_order_to_history(new_order.order_id)
        _save_customers() # Müşteri geçmişini kaydet
        _save_orders() # Yeni siparişi kaydet
        inventory_manager.save_products() # Güncellenmiş stoğu kaydet

        print("\nSipariş başarıyla verildi!")
        new_order.display_order_details(inventory_manager)
        # Müşteriye sipariş hakkında bildirim gönder
        notification_service.notify(
            current_customer.customer_id,
            f"Siparişiniz (ID: {new_order.order_id}) başarıyla verildi. Durum: {new_order.status.value}"
        )
    else:
        print("Sipariş verilemedi. Lütfen stok veya gönderim seçeneklerini kontrol edin.")

def view_order_history():
    """Mevcut müşterinin sipariş geçmişini görüntüler."""
    global current_customer, orders, inventory_manager
    if not current_customer:
        print("Sipariş geçmişinizi görüntülemek için lütfen giriş yapın.")
        return

    print(f"\n--- {current_customer.name} için Sipariş Geçmişi ---")
    if not current_customer.order_history:
        print("Daha önce hiç siparişiniz yok.")
        return

    for order_id in current_customer.order_history:
        order = orders.get(order_id)
        if order:
            order.display_order_details(inventory_manager)
        else:
            print(f"  Sipariş ID {order_id} sistemde bulunamadı.")
    print("------------------------------------")

def add_new_product_cli():
    """
    CLI üzerinden yeni bir ürün eklemeyi sağlar.
    Bu fonksiyon genellikle yönetici (admin) erişimi gerektirebilir.
    """
    global inventory_manager
    print("\n--- Yeni Ürün Ekle ---")
    name = input("Ürün adını girin: ")
    
    while True:
        try:
            price = float(input("Ürün fiyatını girin: "))
            if price <= 0:
                print("Fiyat pozitif bir sayı olmalıdır.")
                continue
            break
        except ValueError:
            print("Geçersiz fiyat değeri. Lütfen bir sayı girin.")

    while True:
        try:
            stock = int(input("Ürün stoğunu girin: "))
            if stock < 0:
                print("Stok negatif olamaz.")
                continue
            break
        except ValueError:
            print("Geçersiz stok değeri. Lütfen bir tam sayı girin.")

    category = input("Ürün kategorisini girin: ")

    # Benzersiz bir ID oluşturma
    # Mevcut en yüksek ID'den bir fazlasını alabiliriz veya UUID kullanabiliriz.
    # UUID daha sağlamdır. İlk 8 karakterini kullanabiliriz.
    product_id = str(uuid.uuid4())[:8] 
    while inventory_manager.get_product(product_id): # ID zaten varsa tekrar oluştur
        product_id = str(uuid.uuid4())[:8]

    new_product = Product(product_id, name, price, stock, category)
    if inventory_manager.add_product(new_product): # InventoryManager'a ekle
        print(f"'{name}' ürünü başarıyla eklendi. ID: {new_product.product_id}")
    else:
        print(f"Hata: '{name}' ürünü eklenemedi.")

def update_order_status_cli():
    """Yönetici benzeri bir kullanıcının sipariş durumunu güncellemesine izin verir."""
    global orders, inventory_manager, notification_service
    print("\n--- Sipariş Durumunu Güncelle (Yönetici Fonksiyonu) ---")
    order_id = input("Güncellenecek Sipariş ID'sini girin: ").strip()
    order = orders.get(order_id)

    if not order:
        print("Sipariş bulunamadı.")
        return

    print(f"Sipariş {order_id} için mevcut durum: {order.status.value}")
    
    # Kullanıcıdan yeni durumu al ve Enum'a dönüştür
    new_status_str = input("Yeni durumu girin (Beklemede, İşleniyor, Gönderildi, Teslim Edildi, İptal Edildi): ").strip()
    
    new_status_enum = None
    for status_member in OrderStatus:
        if status_member.value.lower() == new_status_str.lower():
            new_status_enum = status_member
            break
    
    if new_status_enum is None:
        print("Geçersiz durum girişi. Lütfen belirtilen durumları kullanın.")
        return

    # Sipariş 'İptal Edildi' olarak ayarlanırsa stokları geri al
    if new_status_enum == OrderStatus.CANCELLED:
        if order.cancel_order(inventory_manager):
            # Stok geri alındı ve durum güncellendi, sadece kaydetme ve bildirim kalıyor
            pass
        else:
            print(f"Sipariş {order_id} iptal edilemedi. Stok geri alınmadı.")
            return # Stok geri alınamazsa işlemi durdur
    else:
        order.update_status(new_status_enum) # Diğer durum değişiklikleri için normal güncelleme

    _save_orders() # Güncellenmiş sipariş durumunu kaydet
    inventory_manager.save_products() # Stok değişikliklerini kaydet

    # Müşteriye durum değişikliği hakkında bildirim gönder
    notification_service.notify(
        order.customer_id,
        f"Siparişiniz (ID: {order.order_id}) durumu şuna güncellendi: {order.status.value}"
    )

def admin_menu():
    """Yönetici fonksiyonları için alt menü."""
    while True:
        print("\n--- Yönetici Menüsü ---")
        print("1. Yeni Ürün Ekle")
        print("2. Sipariş Durumunu Güncelle")
        print("3. Geri Dön (Ana Menü)")
        admin_choice = input("Yönetici seçiminizi girin: ").strip()

        if admin_choice == '1':
            add_new_product_cli()
        elif admin_choice == '2':
            update_order_status_cli()
        elif admin_choice == '3':
            print("Ana Menüye dönülüyor.")
            break
        else:
            print("Geçersiz seçim. Lütfen tekrar deneyin.")

def run_cli():
    """Akıllı Kargo Sisteminin ana CLI döngüsünü başlatır."""
    global current_customer
    print("Akıllı Kargo ve Sipariş Yönetim Sistemine Hoş Geldiniz!")
    
    # Uygulama başladığında verileri yükle
    _load_customers()
    _load_orders()

    while True:
        print("\n--- Ana Menü ---")
        if current_customer:
            print(f"Giriş Yapılan Kullanıcı: {current_customer.name} (ID: {current_customer.customer_id})")
            print("1. Ürünlere Göz At")
            print("2. Yeni Sipariş Ver")
            print("3. Sipariş Geçmişini Görüntüle")
            print("4. Yönetici Fonksiyonları")
            print("5. Çıkış Yap")
            print("6. Çık")
        else:
            print("1. Kaydol")
            print("2. Giriş Yap")
            print("3. Ürünlere Göz At")
            print("4. Çık")

        choice = input("Seçiminizi girin: ").strip()

        if current_customer:
            if choice == '1':
                browse_products()
            elif choice == '2':
                place_order()
            elif choice == '3':
                view_order_history()
            elif choice == '4': # Yönetici Fonksiyonları menüsü
                admin_menu()
            elif choice == '5':
                logout_customer()
            elif choice == '6':
                print("Akıllı Kargo Sisteminden çıkılıyor. Güle güle!")
                break
            else:
                print("Geçersiz seçim. Lütfen tekrar deneyin.")
        else: # Giriş yapılmamış
            if choice == '1':
                register_customer()
            elif choice == '2':
                login_customer()
            elif choice == '3':
                browse_products()
            elif choice == '4':
                print("Akıllı Kargo Sisteminden çıkılıyor. Güle güle!")
                break
            else:
                print("Geçersiz seçim. Lütfen tekrar deneyin.")

if __name__ == "__main__":
    # CLI'yi başlat
    run_cli()
