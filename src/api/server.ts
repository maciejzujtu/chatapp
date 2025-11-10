export class WebsocketListener {
    private host = "localhost"
    private port = 8080
    public server = new WebSocket(`ws://${this.host}:${this.port}`)

    async message() {
        this.server.addEventListener('message', async (msg) => {
            console.log(msg.data)
        })
    }

    async open() {
        this.server.addEventListener('open', () => {
            console.log('Connected')
        })
    }

    constructor() {
        this.message()
    }
}