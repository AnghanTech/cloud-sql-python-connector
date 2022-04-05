import ssl
import socket
import platform
from typing import Any, TYPE_CHECKING
from google.cloud.sql.connector.instance import (
    PlatformNotSupportedError,
)

SERVER_PROXY_PORT = 3307

if TYPE_CHECKING:
    import pytds


def connect(ip_address: str, ctx: ssl.SSLContext, **kwargs: Any) -> "pytds.Connection":
    """Helper function to create a pytds DB-API connection object.

    :type ip_address: str
    :param ip_address: A string containing an IP address for the Cloud SQL
        instance.

    :type ctx: ssl.SSLContext
    :param ctx: An SSLContext object created from the Cloud SQL server CA
        cert and ephemeral cert.


    :rtype: pytds.Connection
    :returns: A pytds Connection object for the Cloud SQL instance.
    """
    try:
        import pytds
    except ImportError:
        raise ImportError(
            'Unable to import module "pytds." Please install and try again.'
        )

    db = kwargs.pop("db", None)

    # Create socket and wrap with context.
    sock = ctx.wrap_socket(
        socket.create_connection((ip_address, SERVER_PROXY_PORT)),
        server_hostname=ip_address,
    )
    if kwargs.pop("active_directory_auth", False):
        if platform.system() == "Windows":
            # Ignore username and password if using active directory auth
            server_name = kwargs.pop("server_name")
            return pytds.connect(
                database=db,
                auth=pytds.login.SspiAuth(port=1433, server_name=server_name),
                sock=sock,
                **kwargs,
            )
        else:
            raise PlatformNotSupportedError(
                "Active Directory authentication is currently only supported on Windows."
            )

    user = kwargs.pop("user")
    passwd = kwargs.pop("password")
    return pytds.connect(
        ip_address, database=db, user=user, password=passwd, sock=sock, **kwargs
    )