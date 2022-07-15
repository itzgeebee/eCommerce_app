import pandas as pd
from online_store.models import Product
from online_store import db


class RawData:
    def __init__(self):
        self.laptop_df = pd.read_csv("online_store/jumia_laptop_prices.csv")
        self.phone_df = pd.read_csv("online_store/phone_prices.csv")

        self.laptop_dict = self.laptop_df.to_dict("list")
        self.phone_dict = self.phone_df.to_dict("list")

    def transfer_to_db(self, phon):
        for i in range(len(phon["Spec"])):
            new_product = Product(
                quantity=phon["Quantity"][i],
                product_name=phon["Product_name"][i],
                product_description=phon["Spec"][i],
                category=phon["Category"][i],
                img_url=phon["image_url"][i],
                price=phon['Price'][i]
            )
            db.session.add(new_product)
            db.session.commit()


raw_data = RawData()
ph = raw_data.phone_dict
lap = raw_data.laptop_dict
raw_data.transfer_to_db(ph)
raw_data.transfer_to_db(lap)

