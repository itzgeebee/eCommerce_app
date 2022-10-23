def transform_user_response(new_user):
    return {
                    "id": new_user.id,
                    "first_name": new_user.first_name,
                    "last_name": new_user.last_name,
                    "street": new_user.street,
                    "city": new_user.city,
                    "zip": new_user.zip,
                    "mail": new_user.mail,
                    "phone": new_user.phone,
                    "role": new_user.role
                }