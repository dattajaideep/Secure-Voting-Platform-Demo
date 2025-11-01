import graphviz

def create_architecture_diagram():
    dot = graphviz.Digraph(comment='Secure Voting Platform Architecture')
    dot.attr(rankdir='TB')
    
    # Add nodes
    dot.node('user', 'User Interface\n(Streamlit)')
    dot.node('auth', 'Authentication\n(OAuth)')
    dot.node('crypto', 'Cryptography\n(RSA, Blind Signatures)')
    dot.node('db', 'Database\n(SQLite + RBAC)')
    dot.node('mixnet', 'Mix Network')
    dot.node('audit', 'Audit Logs')
    
    # Add edges
    dot.edge('user', 'auth', 'authenticate')
    dot.edge('auth', 'crypto', 'generate keys')
    dot.edge('user', 'crypto', 'encrypt vote')
    dot.edge('crypto', 'mixnet', 'shuffle')
    dot.edge('mixnet', 'db', 'store')
    dot.edge('db', 'audit', 'log')
    
    # Save the diagram
    dot.render('images/architecture', format='png', cleanup=True)

def create_voting_flow():
    dot = graphviz.Digraph(comment='Voting Flow')
    dot.attr(rankdir='LR')
    
    # Add nodes for voting flow
    dot.node('register', 'Registration')
    dot.node('token', 'Token Request')
    dot.node('vote', 'Vote Casting')
    dot.node('mix', 'Mix Network')
    dot.node('tally', 'Vote Tally')
    
    # Add edges
    dot.edge('register', 'token')
    dot.edge('token', 'vote')
    dot.edge('vote', 'mix')
    dot.edge('mix', 'tally')
    
    # Save the diagram
    dot.render('images/voting-flow', format='png', cleanup=True)

if __name__ == '__main__':
    create_architecture_diagram()
    create_voting_flow()