package services

import (
	"fmt"
	"io/ioutil"
	"net/http"
)


func main() {
	// リクエストの作成
	url := ""
	res, err := http.Get(url)
	if err != nil {
		panic(err)
	}

	defer res.Body.Close() 

	// レスポンス表示
	body, err := ioutil.ReadAll(res.Body)
	if err != nil{
		panic(err)
	}
	fmt.Printf("%s", body)
}