"""
Terminal creation and cleanup.
Utility functions to run a terminal (connected via socat(1)) on each host.

Requires socat(1) and xterm(1).
Optionally uses gnome-terminal.
"""

from subprocess import Popen
from os import environ

from mininet.log import error
from mininet.util import quietRun, errRun

def tunnelX11( node, display=None):
    """Create an X11 tunnel from node:6000 to the root host
       display: display on root host (optional)
       returns: node $DISPLAY, Popen object for tunnel"""
    if display is None:
        display = environ[ 'DISPLAY' ]
    host, screen = display.split( ':' )
    # Unix sockets should work
    if not host or host == 'unix':
        # GDM3 doesn't put credentials in .Xauthority,
        # so allow root to just connect
        quietRun( 'xhost +si:localuser:root' )
        return display, None
    else:
        # Create a tunnel for the TCP connection
        port = 6000 + int( float ( screen ) )
        connection = r'TCP\:%s\:%s' % ( host, port )
        cmd = [ "socat",  "TCP-LISTEN:%d,fork,reuseaddr" % port,
               "EXEC:'mnexec -a 1 socat STDIO %s'" % connection ]
    return 'localhost:' + screen, node.popen( cmd )

def makeTerm( node, title='Node', term='xterm', display=None ):
    """Create an X11 tunnel to the node and start up a terminal.
       node: Node object
       title: base title
       term: 'xterm' or 'gterm'
       returns: two Popen objects, tunnel and terminal"""
    title += ': ' + node.name
    if not node.inNamespace:
        title += ' (root)'
    cmds = {
        'xterm': [ 'xterm', '-title', title, '-display' ],
        'gterm': [ 'gnome-terminal', '--title', title, '--display' ]
    }
    if term not in cmds:
        error( 'invalid terminal type: %s' % term )
        return
    display, tunnel = tunnelX11( node, display )
    term = node.popen( cmds[ term ] + [ display ] )
    return [ tunnel, term ] if tunnel else [ term ]

def cleanUpScreens():
    "Remove moldy socat X11 tunnels."
    errRun( "pkill -9 -f mnexec.*socat" )

def makeTerms( nodes, title='Node', term='xterm' ):
    """Create terminals.
       nodes: list of Node objects
       title: base title for each
       returns: list of created tunnel/terminal processes"""
    terms = []
    for node in nodes:
        terms += makeTerm( node, title, term )
    return terms
