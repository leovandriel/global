Global
======

*Find an earlier date for my Global Entry appointment*

# Usage

Set up a Twilio messaging account. Add IDs and auth token to `.config` file:

    {
        "account_sid": "..",
        "service_sid": "..",
        "auth_token": "..",
        "recipient_phone": "+1..",
        "appointment_stamp": "2021-00-00T00:00"
    }

Run with:

    source venv/bin/activate
    pip install twilio
    ./find

Run on a server in the background using:

    nohup ./find > find.out 2> find.err < /dev/null &

# License

MIT
