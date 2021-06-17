package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
)


func main() {
	// リクエストの作成
	apiKey := os.Getenv("OPEN_WEATHER_MAP_API_KEY")
	cityName := "London"
	url := fmt.Sprintf("http://api.openweathermap.org/data/2.5/forecast?q=%s&appid=%s&lang=ja", cityName, apiKey)
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