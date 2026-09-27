from app.services.linkedin.scopes import parse_linkedin_scopes


def test_parse_linkedin_scopes_accepts_comma_separated_response() -> None:
    scopes = parse_linkedin_scopes("email,openid,profile,w_member_social")
    assert scopes == {"email", "openid", "profile", "w_member_social"}


def test_parse_linkedin_scopes_accepts_spaces_and_url_encoding() -> None:
    scopes = parse_linkedin_scopes("openid+profile%20w_member_social")
    assert scopes == {"openid", "profile", "w_member_social"}
