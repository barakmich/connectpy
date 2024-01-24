package main

import (
	"context"
	"errors"
	"flag"
	"log"
	"net/http"
	"strings"

	svcv1 "github.com/barakmich/connectpyexample/proto/svc/v1"
	"github.com/barakmich/connectpyexample/proto/svc/v1/svcv1connect"
	"github.com/bufbuild/connect-go"
	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"
)

var (
	hostport = flag.String("hostport", "0.0.0.0:5001", "Hostport to connect to")
	grpc     = flag.Bool("grpc", false, "use GRPC")
)

type CapsHandler struct{}

func (c *CapsHandler) Caps(ctx context.Context, req *connect.Request[svcv1.CapsRequest]) (*connect.Response[svcv1.CapsResponse], error) {
	return connect.NewResponse(&svcv1.CapsResponse{
		Msg: strings.ToUpper(req.Msg.Msg),
	}), nil
}

func (c *CapsHandler) MustError(ctx context.Context, req *connect.Request[svcv1.MustErrorRequest]) (*connect.Response[svcv1.MustErrorResponse], error) {
	return nil, connect.NewError(connect.CodeInternal, errors.New(req.Msg.ErrMsg))
}

func main() {
	flag.Parse()

	mux := http.NewServeMux()
	// The generated constructors return a path and a plain net/http
	// handler.
	mux.Handle(svcv1connect.NewCapsServiceHandler(&CapsHandler{}))
	log.Println("Serving on ", *hostport)
	err := http.ListenAndServe(
		*hostport,
		// For gRPC clients, it's convenient to support HTTP/2 without TLS. You can
		// avoid x/net/http2 by using http.ListenAndServeTLS.
		h2c.NewHandler(mux, &http2.Server{}),
	)
	log.Fatalf("listen failed: %v", err)

}
