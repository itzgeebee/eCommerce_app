auth_schema = {
    'required': ['mail', 'password', 'first_name', 'last_name',
                 'street', 'city', 'zip', 'phone'],
    'properties': {
        'mail': {'type': 'string', 'format': 'email'},
        'password': {'type': 'string', 'minLength': 6},
        'first_name': {'type': 'string'},
        'last_name': {'type': 'string'},
        'street': {'type': 'string'},
        'city': {'type': 'string'},
        'zip': {'type': 'string'},
        'phone': {'type': 'string', 'minLength': 10}
    }
}

login_schema = {
    'required': ['mail', 'password'],
    'properties': {
        'mail': {'type': 'string', 'format': 'email'},
        'password': {'type': 'string', 'minLength': 6}
    }
}

forgot_password_schema = {
    'required': ['mail'],
    'properties': {
        'mail': {'type': 'string', 'format': 'email'}
    }
}

change_password_schema = {
    'required': ['old_password', 'new_password', 'confirm_password'],
    'properties': {
        'old_password': {'type': 'string', 'minLength': 6},
        'new_password': {'type': 'string', 'minLength': 6},
        'confirm_password': {'type': 'string', 'minLength': 6}
    }
}

reset_password_schema = {
    'required': ['new_password', 'confirm_password'],
    'properties': {
        'new_password': {'type': 'string', 'minLength': 6},
        'confirm_password': {'type': 'string', 'minLength': 6}
    }
}

update_user_schema = {
    'properties': {
        'first_name': {'type': 'string'},
        'last_name': {'type': 'string'},
        'street': {'type': 'string'},
        'city': {'type': 'string'},
        'zip': {'type': 'string'},
        'phone': {'type': 'string', 'minLength': 10},
        'mail': {'type': 'string', 'format': 'email'}
    }
}

add_product_schema = {
    'required': ['product_name', 'product_description', 'price', 'quantity',
                 'category', 'img_url'],
    'properties': {
        'product_name': {'type': 'string'},
        'product_description': {'type': 'string'},
        'price': {'type': 'number'},
        'quantity': {'type': 'number', 'minimum': 1},
        'category': {'type': 'string'},
        'img_url': {'type': 'string', 'format': 'uri'}
    }
}

update_product_schema = {
    'properties': {
        'product_name': {'type': 'string'},
        'product_description': {'type': 'string'},
        'price': {'type': 'number'},
        'quantity': {'type': 'number', 'minimum': 1},
        'category': {'type': 'string'},
        'img_url': {'type': 'string', 'format': 'uri'}
    }
}

update_role_schema = {
    'required': ['role'],
    'properties': {
        'role': {'type': 'number', 'enum': [1, 2], 'default': 2}
    }
}

add_to_cart_schema = {
    'required': ['prod_id', 'qty'],
    'properties': {
        'prod_id': {'type': 'number'},
        'qty': {'type': 'number', 'minimum': 1}
    }
}

update_cart_schema = {
    'required': ['qty'],
    'properties': {
        'qty': {'type': 'number', 'minimum': 0}
    }
}

add_rating_schema = {
    'required': ['rating', 'review'],
    'properties': {
        'rating': {'type': 'number', 'minimum': 1, 'maximum': 5},
        'review': {'type': 'string'}
    }
}

checkout_schema = {
    'required': ['street', 'city', 'zip'],
    'properties': {
        'street': {'type': 'string'},
        'city': {'type': 'string'},
        'zip': {'type': 'string'}
    }
}
