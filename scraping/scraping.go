package scraping

import (
	"bytes"
	"io/ioutil"
	"net/http"	// GET
	"regexp"	// 正規表現
)

// GoでGETを使ってHTMLを文字列で取得
// 参考：https://saitodev.co/article/Go%E3%81%A7GET%E3%82%92%E4%BD%BF%E3%81%A3%E3%81%A6HTML%E3%82%92%E6%96%87%E5%AD%97%E5%88%97%E3%81%A7%E5%8F%96%E5%BE%97%E3%81%97%E3%81%A6%E3%81%BF%E3%82%8B/
func getHTML(url string) string {
	res, err := http.Get(url)	// 対象URLにGETを送り、結果をres変数に代入

	if err != nil{
		panic(err)	// エラーがあればプログラムを停止させるランタイムエラーを作成
	}

	// 処理が最後まで実行されたら、res.Bodyをcloseする用に設定
	defer res.Body.Close()

	// HTMLの箇所だけ取得
	body, err := ioutil.ReadAll(res.Body)
	if err != nil {
		panic(err)
	}

	// byteデータを文字列へ変換する
	buf := bytes.NewBuffer(body)
	html := buf.String()

	return html
}

// 渡されたHTMLから運行情報を切り出し
func GetTrainInfo(url string) string {
	html := getHTML(url)	// URLからHTML情報の取得

	// 「`」(バッククォート)を用いることで、バッククォート以外の改行を含めたすべての文字を使用
	// (ダブルクォートでは、\によるエスケープを使用しなければならない)
	// <dd>タグにカッコまれた要素を取得(class="trouble"は何かしらの遅延が発生)
	r := regexp.MustCompile(`<dd class="trouble">([.\s\S]*?)</dd>`)	// 正規オブジェクトの生成
	// 正規表現に該当する箇所のテキスト取得
	res_dd := r.FindAllStringSubmatch(html, -1)

	// テキストが取得できなければ
	if len(res_dd) == 0{
		return "遅延はありません。"
	} else{
		// 遅延情報を整形
		r = regexp.MustCompile(`<p>(.*?)<span>(.*?)</span></p>`)	
		res := r.FindAllStringSubmatch(res_dd[0][1], -1)
		return res[0][1] + res[0][2]	// 遅延情報詳細 + 掲載日時
	}
}

////////////////////
// main関数での使用法

// https://transit.yahoo.co.jp/traininfo/top より各路線の運行情報が
// 記載されたページのURLを取得

// import(
// 		"main.go/scraping"
// )

// func main(){
// 	// 京浜東北根岸線
// 	fmt.Println("京浜東北根岸線")
// 	url := "https://transit.yahoo.co.jp/traininfo/detail/22/0/"
// 	trainInfo := getTrainInfo(url)
	
// 	// 横須賀線
// 	fmt.Println("横須賀線")
// 	url = "https://transit.yahoo.co.jp/traininfo/detail/29/0/"
// 	trainInfo := getTrainInfo(url)
