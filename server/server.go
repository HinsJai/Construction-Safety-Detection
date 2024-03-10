package main

import (
	"log"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
)

type response struct {
	Message string `json:"message"`
}

var (
	app *fiber.App
)

func setup_get(app *fiber.App) {
	// Setup route
	app.Get("/sendstring", func(c *fiber.Ctx) error {

		response := response{Message: "Hello from Go Fiber!"}
		return c.JSON(response)
	})
}

func start_server() {
	if err := app.Listen("127.0.0.1:8080"); err != nil {
		log.Fatalf("Error starting server: %v", err)
	}
}

func main() {
	app = fiber.New()
	app.Use(cors.New(cors.Config{
		AllowOrigins: "*",
		AllowHeaders: "*",
		AllowMethods: "*",
	}))

	setup_get(app)
	start_server()

}
