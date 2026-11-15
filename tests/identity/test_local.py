from newsimpact.identity.adapters.local import LocalSingleUser


def test_local_sign_in_is_one_admin_user() -> None:
    user = LocalSingleUser().user_for(None)
    assert user is not None and user.user_id == "local" and user.is_admin
