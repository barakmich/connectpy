package main

import (
	"context"
	"crypto/tls"
	"flag"
	"log"
	"net"
	"net/http"

	svcv1 "github.com/barakmich/connectpyexample/proto/svc/v1"
	"github.com/barakmich/connectpyexample/proto/svc/v1/svcv1connect"
	"github.com/bufbuild/connect-go"
	"golang.org/x/net/http2"
)

var (
	hostport = flag.String("hostport", "127.0.0.1:5001", "Hostport to connect to")
	grpc     = flag.Bool("grpc", false, "use GRPC")
	msg      = flag.String("msg", "hello world", "Message to send over RPC")
)

func main() {
	flag.Parse()
	var client svcv1connect.CapsServiceClient
	if *grpc {
		log.Println("Connecting with GRPC")
		client = svcv1connect.NewCapsServiceClient(newInsecureClient(), "http://"+*hostport, connect.WithGRPC())
	} else {
		log.Println("Connecting with HTTP")
		client = svcv1connect.NewCapsServiceClient(http.DefaultClient, "http://"+*hostport)
	}
	resp, err := client.Caps(context.Background(), connect.NewRequest(&svcv1.CapsRequest{Msg: *msg}))
	if err != nil {
		log.Fatalln("Got error when expected Caps response", err)
	}
	log.Println("Got Caps response!", resp.Msg.Msg)
	_, err = client.MustError(context.Background(), connect.NewRequest(&svcv1.MustErrorRequest{ErrMsg: "this is inside the Go err_msg"}))
	if err == nil {
		log.Fatalln("MustError succeeded?")
	}
	log.Println("Got error!", err)
}

func newInsecureClient() *http.Client {
	return &http.Client{
		Transport: &http2.Transport{
			AllowHTTP: true,
			DialTLS: func(network, addr string, _ *tls.Config) (net.Conn, error) {
				// If you're also using this client for non-h2c traffic, you may want
				// to delegate to tls.Dial if the network isn't TCP or the addr isn't
				// in an allowlist.
				return net.Dial(network, addr)
			},
			// Don't forget timeouts!
		},
	}
}
