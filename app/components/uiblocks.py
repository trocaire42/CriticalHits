import reflex as rx

class InfiniteScroll(rx.Component):
    library = "react-infinite-scroll-component"
    tag = "InfiniteScroll"
    is_default = True
    data_length: rx.Var[int]
    has_more: rx.Var[bool]
    next: rx.EventHandler
    loader: rx.Component
    end_message: rx.Component
