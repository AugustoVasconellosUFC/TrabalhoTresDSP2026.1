classDiagram
    Usuario "1" --> "0..*" Endereco : embutido
    Usuario "0..*" --> "0..*" Loja : lojas_favoritas
    Loja "1" --> "0..*" Produto : tem
    Pedido "1" --> "1" Usuario : realizado_por
    Pedido "1" --> "1..*" ItemPedido : embutido
    Produto "1" --> "0..*" Documento : possui