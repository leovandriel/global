Global
======

*Find an earlier date for my Global Entry appointment*

# Usage

Set up a Twilio messaging account. Add IDs and auth token to `config.env` file:

    account_sid='..'
    service_sid='..'
    auth_token='..'
    cloud_path='..'
    hash_salt='..'

Run with:

    ./run

Add a user's phone-number, name, and max-appointment-date:

    add_recipient('+1..', '..', '2021-01-01T00:00')

# License

MIT
