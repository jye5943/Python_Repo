########################################################################################################################
# blockChain V 2.0
# 수정한 이 :   박재원
# 수정 날짜 :   2019.05.18
# 추가 내용 :
#  - Do_GET에 /txData 와 /txData/getTxData 추가.
#  - Do_POST에 /block/syncTx 추가.
#  - 서버들간 txData 동기화 가능하게 수정.
# 수정 내용 :
#  - txData Class에 변수가 추가됨으로써 수정해야할 모든 부분 수정.
#  - getTxData()와 readTx() 분리.
#  - getTxData()를 txData 객체리스트를 받아 하나의 문자열로 변환하고 반환게끔 수정.
#  - readTx()에 mode를 추가하여 모든 txData가 필요한 경우(external)와  commitYN가 0인 txData만 필요한 경우(internal)로 분리.
#  - txData.fee 기준 정렬 제대로 안 된 부분 재수정.
#  - readTx()를 처음부터 txData에서 block에 담을 수 있는 최대 개수만 순차적으로 가져와 리스트에 담아 반환하게끔 수정.
#  - calcuateMerkleHash 부분을 위의 수정사항으로 인하여 전면 재수정.
########################################################################################################################
import hashlib
import time
import csv
import random
from http.server import BaseHTTPRequestHandler, HTTPServer  # 이거 파이썬 3.0버전에서만 사용가능함
from socketserver import ThreadingMixIn
import json
import re
from urllib.parse import parse_qs
from urllib.parse import urlparse
import threading
import cgi
import uuid
from tempfile import NamedTemporaryFile
import shutil
import requests  # for sending new block to other nodes

PORT_NUMBER = 8096
g_txFileName = "txData.csv"
g_bcFileName = "blockchain.csv"
g_nodelstFileName = "nodelst.csv"
g_receiveNewBlock = "/node/receiveNewBlock"
g_difficulty = 2
g_maximumTry = 100
# -----------------------------------------V01 : 완
# 최대 보유 거래내역 증가
g_maximumGetTx = 50
g_nodeList = {'127.0.0.1': '8099'}  # trusted server list, should be checked manually

class Block:

    def __init__(self, index, previousHash, timestamp, data, currentHash, proof, merkleHash):
        self.index = index
        self.previousHash = previousHash
        self.timestamp = timestamp
        self.data = data
        self.currentHash = currentHash
        self.proof = proof
        # -----------------------------------------V01 : 완
        # 머클트리로 추출한 해쉬
        self.merkleHash = merkleHash

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class txData:

    def __init__(self, commitYN, sender, amount, receiver, fee, uuid, transactionTime):
        self.commitYN = commitYN
        self.sender = sender
        self.amount = amount
        self.receiver = receiver
        self.fee = fee
        self.uuid = uuid
        self.transactionTime = transactionTime

    # block과 hash를 생성해서 block 객체에 담아서 리턴한다


def generateGenesisBlock():
    print("generateGenesisBlock is called")

    # teimestamp는 1970년 1월1일 자정 이후로 초단위로 측정한 절대시간을 의미하는 단순변수이며,
    # 이 변수에 time.time()으로 위에서부터 누적된 초를 float자료형으로 반환하여 대입한다.
    timestamp = time.time()
    # 불러온 시간 확인
    print("time.time() => %f \n" % timestamp)
    # hash생성
    txDataList = readTx(g_txFileName)
    merkleHash = calculateMerkleHash(txDataList)

    # -----------------------------------------V01 : 완
    #블록 hash생성에 merkleHash 추가
    tempHash = calculateHash(0, '0', timestamp, 0, merkleHash)
    print(tempHash)
    # -----------------------------------------V01 : 완
    # 이부분에 merkleHash를 추가시켜 반환한다. 총 7개
    # genesis block의 생성부터 거래원장의 고유넘버가 존재하기때문에 그걸 가져와서 blockdata에 넣어준다.
    txDataList = readTx(g_txFileName)
    genesisblockData = getTxData(txDataList)
    return Block(0, '0', timestamp, genesisblockData, tempHash, 0, merkleHash)


# 입력받은 인자들을 str자료형으로 캐스팅하고 한 문장으로 value에 저장하여 value를 기반으로 해쉬값을 만든다.
# -----------------------------------------V01 : 완
# data를 빼고 merkleHash를 추가시켜 해쉬를 생성
def calculateHash(index, previousHash, timestamp, proof, merkleHash):
    value = str(index) + str(previousHash) + str(timestamp) + str(proof) + merkleHash
    # 인자로 받은 모든 데이터를 차례대로 더한 value 문자열을 utf-8로 인코딩한후 hashlib.sha256를 통해 해쉬암호화한다
    # sha256은 암호학적 해쉬함수의 한 종류. utf-8로 인코딩을 하지않고 쓰면 에러난다. 반환값은 hash객체.hash자료형 아니다. 객체다
    sha = hashlib.sha256(value.encode('utf-8'))
    # hash객체에서 제공하는 hexdigest() 메소드는 오직 16진수숫자만 포함하는 이중길이(?)의 해쉬값을 문자열로 변환하여 반환한다.
    return str(sha.hexdigest())

#-----------------------------------------V01 : 완
# 머클해쉬추출 작성
#-----------------------------------------V02 : 완
# txData객체 리스트를 받아 문자열 리스트로 변환 후 rcGetMerkleHash에 인자로 던지게끔 수정.
def calculateMerkleHash(importedTx) :
    #txData객체 리스트를 문자열 리스트로 변환
    txDataList = []
    print("hash merkling..................")
    if len(importedTx) > 0:
        for i in importedTx:
            print(i.__dict__)
            transaction = "[" + i.uuid + "]" "UserID " + i.sender + " sent " + i.amount + " bitTokens to UserID " + i.receiver + " fee "+ i.fee + ". "  #
            print(transaction)
            txDataList.append(transaction)
    #문자열 리스트를 머클트리 재귀함수에 던져준다.
    return rcGetMerkleHash(txDataList)


 # -----------------------------------------V01 : 완
 # 머클트리해쉬 재귀함수. target = txData의 문자열 리스트
def rcGetMerkleHash(target) :
    strBinaryTxData = ""
    #check
    print("current len of Target =  " + str(len(target)))
    endIndexOfTarget = len(target) - 1
    #taget의 원소가 1개라면 종료.
    if len(target) <= 1 :
        sha = hashlib.sha256(target[0].encode('utf-8'))
        return str(sha.hexdigest())
    #1개 이상이라면 1개가 될때까지 계속 해쉬화
    else :
        newTarget = []
        for i in range(endIndexOfTarget - 1):
            if i % 2 == 0 :
                strBinaryTxData = strBinaryTxData + target[i] + target[i+1]
                sha = hashlib.sha256(target[i].encode('utf-8'))
                newTarget.append(str(sha.hexdigest()))

        #target리스트의 길이가 홀수라면
        if (len(target) % 2) != 0:
            sha = hashlib.sha256(target[endIndexOfTarget].encode('utf-8'))
            newTarget.append(str(sha.hexdigest()))
        #짝수라면
        else :
            strBinaryTxData = strBinaryTxData + target[endIndexOfTarget-1] + target[endIndexOfTarget]
            sha = hashlib.sha256(strBinaryTxData.encode('utf-8'))
            newTarget.append(str(sha.hexdigest()))
        #재귀   
        return rcGetMerkleHash(newTarget)

def calculateHashForBlock(block):
    # -----------------------------------------V01 : 완
    # data대신 머클트리로 생성한 해쉬를 추가
    return calculateHash(block.index, block.previousHash, block.timestamp, block.proof, block.merkleHash)


def getLatestBlock(blockchain):
    return blockchain[len(blockchain) - 1]

# -----------------------------------------V01 : 완
# -----------------------------------------V02 : 완
# blockData를 이 fucntion에서 가져와 merkleHash를 추출하여 블록을 생성하게 바꾼다.
def generateNextBlock(blockchain, timestamp, proof):
    previousBlock = getLatestBlock(blockchain)
    nextIndex = int(previousBlock.index) + 1
    nextTimestamp = timestamp
    #blockdata 가져오기
    txDataList = readTx(g_txFileName)
    strTxData = getTxData(txDataList)
    #머클해쉬 생성
    merkleHash = calculateMerkleHash(txDataList)
    # -----------------------------------------V01 : 완
    # 이부분의 blockData를 merkleHash로 바꿔준다
    nextHash = calculateHash(nextIndex, previousBlock.currentHash, nextTimestamp, proof, merkleHash)
    # index, previousHash, timestamp, data, currentHash, proof, merkleHash
    # -----------------------------------------V01 : 완
    # block 객체에 merklehash를 추가한다.
    return Block(nextIndex, previousBlock.currentHash, nextTimestamp, strTxData, nextHash, proof, merkleHash)

# parameter또한 block객체list이다.
def writeBlockchain(blockchain):
    # list
    blockchainList = []

    # blockchain의 block객체들을 순차적으로 해체 하여 blockList에 담는다. 이때 blockList는 list 자료형이며,
    # blockchainList은 이러한 list들의 list이다. 즉 list자료형변수들의 list.
    # block객체list들의 block자료형 객체들의 변수들을 list형 변수에 차례로 담고, 그 list형 변수들을 차례로 list자료형 list에 담는 과정임.
    # 이러한 귀찮은 과정을 거치는 이유는 blockchain.csv파일에 block의 내용을 문자열 형태로 하나하나 저장해주기 위해 이 과정을 거치는 거임.
    # -----------------------------------------V01 : 완
    # blockList에 block.merkleHash 추가한다.
    for block in blockchain:
        blockList = [block.index, block.previousHash, str(block.timestamp), block.data, block.currentHash, block.proof, block.merkleHash]
        blockchainList.append(blockList)

    # [STARAT] check current db(csv) if broadcasted block data has already been updated
    lastBlock = None
    try:
        # 'bloackchain.csv'파일을 'r'(읽기)모드로 file의 별칭을 주어 스트림을 연다. 여기서 csv파일이 존재하지않으면 except로 빠진다.
        # 최초로 block를 생성할때는, csv파일이 존재하지 않으므로 except로 빠진다.
        with open(g_bcFileName, 'r', newline='') as file:
            blockReader = csv.reader(file)
            last_line_number = row_count(g_bcFileName)
            for line in blockReader:
                if blockReader.line_num == last_line_number:
                    # -----------------------------------------V01 : 완
                    # line[6] 추가.
                    lastBlock = Block(line[0], line[1], line[2], line[3], line[4], line[5], line[6])

        # 채굴에 성공하여 db에 쓰려고 할때, 채굴되었다는 요청을 받으면 버린다.
        # 가장 최근 블록의 인덱스 + 1(막 방금 채굴한) 블록체인 리스트의 가장 마지막 블록체인과의 인덱스가 같지 않으면
        if int(lastBlock.index) + 1 != int(blockchainList[-1][0]):
            print("index sequence mismatch")
            # 가장 최근 블록이 블록체인 리스트의 가장 마지막 블록체인과의 인덱스가 같으면
            if int(lastBlock.index) == int(blockchainList[-1][0]):
                print("db(csv) has already been updated")
            return
    except:
        print("file open error in check current db(csv) \n or maybe there's some other reason")
        # pass는 실행 할 것이 아무 것도 없다는 것을 의미. 따라서 아무런 동작을 하지 않고 다음 코드를 실행.
        # except바깥의 아래 코드로 이동한다.
        pass
        # return
    # [END] check current db(csv)

    # 'bloackchain.csv'파일을 'w'(쓰기)모드로 file의 별칭을 주어 스트림을 연다.
    # 'w'(쓰기)모드의 경우, 파일이 존재하면 원래 있던 내용이 모두 사라지고, 파일이 존재하지 않는 경우 새로운 파일이 생성된다.
    # 즉, 최초의 블록, genesis block이 생성되는 경우 blockchain.csv 파일은 이 곳에서 최초로 생성이 되는 것임.
    # 또한, as file : 의 : 를 꼭 기억하자. 아마도 파일스트림을 열고 해야할 작업을 마치면 자동으로 닫히게 되는 구조인가 보다.
    with open(g_bcFileName, "w", newline='') as file:
        # 이곳에서 최초로 생성한 blockchain.csv에 block객체의 내용을 순차적으로 담은 list변수를 담은 list변수의 list인 blockchainList에서
        # list변수들을 차례대로 해당 변수의 내용들을 csv파일에 '라인단위'로 저장해준다. 그것을 해주는 메소드가 writerows이다.
        # writerow(리스트)는 하나의 리스트변수만 해주고, writerows(리스트)는 리스트 안에 존재하는 모든 list형 변수를 차례로 저장해준다.
        # 참고사이트 : http://zetcode.com/python/csv/ =>근데 영어임 ㅠㅠ. 그래도 이해하기 쉬움
        writer = csv.writer(file)
        writer.writerows(blockchainList)

    # update txData cause it has been mined.
    # block이 최초로 생성되는 경우, 거래내역 자체가 없으므로 걍 패스. 거래내역이 있다면 "txdata.csv"에서 해당 블록체인의 해쉬가 존재하는경우
    # 해당 블록체인에 해당하는 행(row) 첫번째 컬럼 값(ow[0])을 1로 바꿔준다. 근데 또 해당 블록체인의 해쉬값이 txdata.csv에 존재하지 않으면
    # 아무것도 하지 않는다. 의문                                                                                   ????????????????????????????
    for block in blockchain:
        updateTx(block)

    print('Blockchain written to blockchain.csv.')
    print('Broadcasting new block to other nodes')
    #block가 생성이 되었으므로 모든 node들에게 생성되었음을 알린다.
    broadcastNewBlock(blockchain)

# mode의 초기값은 internal이므로, mode가 명시되어있지 않는 경우, blockchain.csv파일이 존재하지 않을 때, except로 빠져
# internal에 해당하는 if문이 실행된다.
def readBlockchain(blockchainFilePath, mode='internal'):
    print("readBlockchain")
    importedBlockchain = []

    try:
        # blockchainFilePath = 'blcokchain.csv' 즉, 해당 파일을 'r' 읽기 형태로 file이라는 별칭(객체)으로 연다.
        with open(blockchainFilePath, 'r', newline='') as file:
            # csv.reader(별칭)이 성공하면 reader객체를 리턴한다.
            blockReader = csv.reader(file)
            # file의 한 라인씩을 가져온다.
            for line in blockReader:
                # -----------------------------------------V01 : 04 완
                # line[6] 추가.
                block = Block(line[0], line[1], line[2], line[3], line[4], line[5], line[6])
                importedBlockchain.append(block)

        print("Pulling blockchain from csv...")

        return importedBlockchain

    # 가장 맨처음에 데이터확인url을 날리는 경우,  'blockchain.csv' 파일이 존재하지 않으므로 csv.reader에서 예외처리로 넘어오게된다.
    except:
        # 현재 모드가 internal(내부)이라면, 새로운 블록을 생성한다.
        if mode == 'internal':
            # -----------------------------------------V01 : 완
            # genesis block 생성부터 txData.csv를 유지한다.
            tempList = []
            tempDict = {"sender": "Genesis Block", "amount": "1000", "receiver": "Hwang", "fee": "50"}
            tempList.append(tempDict)
            res = newtx(tempList)
            # -----------------------------------------V01 : 01 완
            # txData가 제대로 만들어 졌다면
            if res == 1:
                blockchain = generateGenesisBlock()
                # 생성된 블록을 importedBlockchain의 block객체list에 넣는다.
                importedBlockchain.append(blockchain)
                # block객체list를 인자로 던진다.
                writeBlockchain(importedBlockchain)

            return importedBlockchain



        # 현재 모드가 external(외부)이라면,
        else:
            # None 리턴
            return None


# block객체의
def updateTx(blockData):
    # 정규표현식 설정
    phrase = re.compile(
        r"\w+[-]\w+[-]\w+[-]\w+[-]\w+")  # [6b3b3c1e-858d-4e3b-b012-8faac98b49a8]UserID hwang sent 333 bitTokens to UserID kim.
    # block객체의 data field에서 해당 정규표현식과 매칭되는 부분을 전부 찾는다. data는 string 변수.
    # 주의할 점은, block 최초로 생성되었 때의 block인 genesis Block의 data는 "genesis Block"이므로, matchList는 결과적으로 아무것도 들어있지 않는
    # 상태이다. 다만, block이 최초로 생성되는 상황에서는 거래가 있을수가 없기 때문인지, 아니면 genesis Block은 그자체로 거래불가인지는 모르겠음.
    matchList = phrase.findall(blockData.data)

    # 해당 block객체가 거래내역(data)이 없는 경우
    if len(matchList) == 0:
        print("No Match Found! " + str(blockData.data) + "block idx: " + str(blockData.index))
        # block의 data field 에서 거래내역을 찾지 못했으므로 바로 리턴
        return
    # 거래내역이 있으면 이쪽으로 코드가 계속 진행된다.
    # data 내에 정규표현식에 해당하는 문자열, 즉 거래내역이 존재하는 경우, 임시로 파일 스트림을 연다.
    # 임시로 여는 파일은 scope안에서면 사용되고 사라진다.
    # 왜 임시로 열었는지는 의문. 왜 임시로 열고 저장은 하는지는 의문. 왜 임시로 열었는데 delete = false인지는 의문     ???????????????????????
    # 참고사이트 : https://medium.com/@silmari/python-tempfile-%EC%9E%84%EC%8B%9C%ED%8C%8C%EC%9D%BC-%EB%B0%8F-%ED%8F%B4%EB%8D%94-%EB%A7%8C%EB%93%A4%EA%B8%B0-86ea533086ce
    tempfile = NamedTemporaryFile(mode='w', newline='', delete=False)

    # "txdata.csv"파일을 읽기용과 쓰기용으로 각각 파일스트림을 연다. as 뒤에, 위에서 쓴 tempfile이 여기서도 쓰여질수 있는지는 의문           ???????????????????
    with open(g_txFileName, 'r') as csvfile, tempfile:
        reader = csv.reader(csvfile)
        writer = csv.writer(tempfile)
        # 각 행들을 순차적으로 읽어들여와
        for row in reader:
            # -----------------------------------------V01 : 01 완
            # row[4] -> row[5]
            if row[5] in matchList:
                print('updating row : ', row[5])
                # 이 값이 정확히 무엇을 의미하는지는 모르겠으나, 다른 컬럼의 값은 그대로 유지하면서, row[0]만 1로 바꿔주고( 이부분을 업데이트하는 거임)
                row[0] = 1
            # "txdata.csv'에 matchList의 해쉬코드가 있으면, 위의 작업을 하고, 없으면 아무것도 하지않는 채로 이전 데이터 그대로 쓰기용 파일에 저장한다.
            writer.writerow(row)

    # 파일을 이동시키는 shutil.move를 이용해 덮어씌운다. tempfile.name의 내용이 g_txFileName으로 덮어씌워지고, tempfile.name은 존재하지 않는다.
    shutil.move(tempfile.name, g_txFileName)
    # 파일스트림을 닫는다. 위에서 with ~ as 구문으로 자동으로 close()되게 되있는데 여기서 또 닫는지는 의문.          ????????????????????
    csvfile.close()
    tempfile.close()
    print('txData updated')


def writeTx(txRawData):
    print(g_txFileName)
    txDataList = []
    for txDatum in txRawData:
        txList = [txDatum.commitYN, txDatum.sender, txDatum.amount, txDatum.receiver, txDatum.fee, txDatum.uuid, txDatum.transactionTime]
        txDataList.append(txList)

    tempfile = NamedTemporaryFile(mode='w', newline='', delete=False)
    try:
        with open(g_txFileName, 'r', newline='') as csvfile, tempfile:
            reader = csv.reader(csvfile)
            writer = csv.writer(tempfile)
            for row in reader:
                if row:
                    writer.writerow(row)
            # adding new tx
            writer.writerows(txDataList)
        shutil.move(tempfile.name, g_txFileName)
        csvfile.close()
        tempfile.close()
    except:
        # this is 1st time of creating txFile
        try:
            with open(g_txFileName, "w", newline='') as file:
                writer = csv.writer(file)
                writer.writerows(txDataList)
        except:
            return 0
    return 1
    print('txData written to txData.csv.')

# -----------------------------------------V02 : 완
# 거래내역에서 column[0]의 값이 '0' 인 거래내역부터 순차적으로 가져온다.
# 블록생성시의 txData와 txData내역 자체를 요청했을 떄의 txData 부분을 나눈다.
def readTx(txFilePath, mode='internal'):
    importedTx = []
    zeroCount = 0;
    getAllTxData = False

    if mode == 'external' :
        getAllTxData = True

    print("readTx. mode : " + mode)
    try:
        with open(txFilePath, 'r', newline='') as file:

            txReader = csv.reader(file)
            print("file open completed.")

            for row in txReader :
                # -----------------------------------------V02 : 완
                # mode ="internal" 인 경우(commitYn이 0인 row가 필요한 경우)
                if not getAllTxData :
                    print("여기도 테스트")
                    # -----------------------------------------V02 : 완
                    # block에 담을 수 있는 최대 거래내역 개수를 초과하면 중단.
                    if zeroCount < g_maximumGetTx :
                        print("여기도 테스트2, zeroCount = " + str(zeroCount))
                        if row[0] == '0' :  # find unmined txData
                            print("여기도 테스트3")
                            # -----------------------------------------V01 : 완
                            # row[5] 추가
                            # -----------------------------------------V02 : 완
                            # row[6] 추가
                            line = txData(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                            zeroCount = zeroCount + 1
                            print("여기도 테스트4")
                        #개조심... try안에 if에 else가 안달려있으니까 바로 exception으로 빠지더라.
                        else : continue
                # mode = "external" 인 경우(모든 txData가 필요한 경우)
                else :
                    line = txData(row[0], row[1], row[2], row[3], row[4], row[5], row[6])

                importedTx.append(line)
        # mode ="internal" 인 경우(commitYn이 0인 row가 필요한 경우) 정렬을 해준다.
        if not getAllTxData :
            # 수수료가 큰 거래내역으로 정렬
            sortedTxDataList = sorted(importedTx, key=lambda txData: int(txData.fee), reverse=True)
        else :
            sortedTxDataList = importedTx

        print("Pulling txData from csv...")
        print("length : " + str(len(sortedTxDataList)))
        return sortedTxDataList
    except:
        print("Reading txData error..........")
        return []

# "txdata.csv"파일을 읽어와 거래내역을 전체를 string으로 캐스팅하여 반환한다.
def getTxData(importedTx):
    strTxData = ''
    # importedTx의 값이
    if len(importedTx) > 0:
        for i in importedTx:
            print(i.__dict__)
            transaction = "[" + i.uuid + "]" "UserID " + i.sender + " sent " + i.amount + " bitTokens to UserID " + \
                          i.receiver + " fee "+ i.fee + " transaction time " + i.transactionTime + ". "
            print(transaction)
            strTxData += transaction

    return strTxData

def mineNewBlock(difficulty=g_difficulty, blockchainPath=g_bcFileName):
    importedTx = readTx(g_txFileName)
    strTxData = getTxData(importedTx)
    if strTxData == '':
        #genesis Blcok 생성
        blockchain = readBlockchain(blockchainPath)

        if len(blockchain) > 0 and len(blockchain) < 2:
            print("Genesis block is mined.")
        else :
            print("Failed to create Genesis block.")
        return

    blockchain = readBlockchain(blockchainPath)
    timestamp = time.time()
    proof = 0
    newBlockFound = False

    print('Mining a block...')

    while not newBlockFound:
        newBlockAttempt = generateNextBlock(blockchain, timestamp, proof)
        if newBlockAttempt.currentHash[0:difficulty] == '0' * difficulty:
            stopTime = time.time()
            timer = stopTime - timestamp
            print('New block found with proof', proof, 'in', round(timer, 2), 'seconds.')

            newBlockFound = True
        else:
            proof += 1

    blockchain.append(newBlockAttempt)
    writeBlockchain(blockchain)

# mineNewBlock() : 294
def mine():
    mineNewBlock()

# -----------------------------------------V01 : 완
# 비교 대상에 merkleHash 추가
def isSameBlock(block1, block2):
    if str(block1.index) != str(block2.index):
        return False
    elif str(block1.previousHash) != str(block2.previousHash):
        return False
    elif str(block1.timestamp) != str(block2.timestamp):
        return False
    elif str(block1.data) != str(block2.data):
        return False
    elif str(block1.currentHash) != str(block2.currentHash):
        return False
    elif str(block1.proof) != str(block2.proof):
        return False
    elif str(block1.merkleHash) != str(block.merkleHash):
        return False
    return True


# 외부에서 받은 블록들을 비교한다(순서 6개의 경우: [1,2], [2,3] ... [5,6]
def isValidNewBlock(newBlock, previousBlock):
    if int(previousBlock.index) + 1 != int(newBlock.index):
        print('Indices Do Not Match Up')
        return False
    # 체이닝이 맞는지
    elif previousBlock.currentHash != newBlock.previousHash:
        print("Previous hash does not match")
        return False
    # 해쉬검증
    elif calculateHashForBlock(newBlock) != newBlock.currentHash:
        print("Hash is invalid")
        return False
    elif newBlock.currentHash[0:g_difficulty] != '0' * g_difficulty:
        print("Hash difficulty is invalid")
        return False
    return True


def newtx(txToMining, mode='new'):
    newtxData = []
    if mode == 'new' :
        print("newTxData")
        # transform given data to txData object
        for line in txToMining:
            # -----------------------------------------V02 : 완
            # txData생성시 거래시간 추가
            tx = txData(0, line['sender'], line['amount'], line['receiver'], line['fee'], uuid.uuid4(), time.time())
            newtxData.append(tx)

        # limitation check : max 5 tx
        if len(newtxData) > 5:
            print('number of requested tx exceeds limitation')
            return -1

        if writeTx(newtxData) == 0:
            print("file write error on txData")
            return -2

        syncTxBetweenSvr(newtxData)
    #mode가 'sync'인경우
    else :
        print("sync TxData")
        for line in txToMining:
            # -----------------------------------------V02 : 완
            # mode가 'sync'이면 바로 write
            tx = txData(line['commitYN'], line['sender'], line['amount'], line['receiver'], line['fee'], line['uuid'], line['transactionTime'])
            newtxData.append(tx)
            writeTx(newtxData)
    return 1

 # -----------------------------------------V02 : 실패
 # g_nodeList의 목록을 읽어와 txData가 추가될 때마다 동기화 시킨다.
def syncTxBetweenSvr(newTxData) :

    reqHeader = {'Content-Type': 'application/json; charset=utf-8'}
    reqBody = []
    reqBody.append(newTxData)

    for key, value in g_nodeList.items():
        try:
            URL = "http://" + key + ":" + value + "/block/syncTx"
            res = requests.post(URL, headers=reqHeader, data=json.dumps(reqBody))

            if res.status_code == 200:
                print(URL + " sent ok.")
                print(newTxData)
                print("Response Message " + res.text)
            else:
                print(URL + " responding error " + res.status_code)
        except:
            print("Trusted Server " + URL + " is not responding.")

def isValidChain(bcToValidate):
    genesisBlock = []
    bcToValidateForBlock = []

    # Read GenesisBlock
    try:
        with open(g_bcFileName, 'r', newline='') as file:
            blockReader = csv.reader(file)
            for line in blockReader:
                block = Block(line[0], line[1], line[2], line[3], line[4], line[5], line[6])
                genesisBlock.append(block)
    #                break
    except:
        print("file open error in isValidChain")
        return False

    # transform given data to Block object
    for line in bcToValidate:
        # print(type(line))
        # index, previousHash, timestamp, data, currentHash, proof
        block = Block(line['index'], line['previousHash'], line['timestamp'], line['data'], line['currentHash'],
                      line['proof'], line['merkleHash'])
        bcToValidateForBlock.append(block)

    # if it fails to read block data  from db(csv)
    if not genesisBlock:
        print("fail to read genesisBlock")
        return False

    # compare the given data with genesisBlock
    if not isSameBlock(bcToValidateForBlock[0], genesisBlock[0]):
        print('Genesis Block Incorrect')
        return False

    # tempBlocks = [bcToValidateForBlock[0]]
    # for i in range(1, len(bcToValidateForBlock)):
    #    if isValidNewBlock(bcToValidateForBlock[i], tempBlocks[i - 1]):
    #        tempBlocks.append(bcToValidateForBlock[i])
    #    else:
    #        return False

    for i in range(0, len(bcToValidateForBlock)):
        if isSameBlock(genesisBlock[i], bcToValidateForBlock[i]) == False:
            return False

    return True


# 노드를 추가하는 메소드.인자는 요청받은 곳의 ip주소와 port번호
def addNode(queryStr):
    # save
    txDataList = []
    # ip주소와 port번호와 함께 추가적으로 연결시도횟수를 리스트에 입력한다. 처음은 당연히 0.
    txDataList.append([queryStr[0], queryStr[1], 0])  # ip, port, # of connection fail
    # 쓰기용으로 임시파일스트림을 연다.
    tempfile = NamedTemporaryFile(mode='w', newline='', delete=False)
    # 읽기용으로 "nodelst.csv" 파일스트림을 연다. 단, 해당 파일이 존재하지않으면 except로 빠진다.
    try:
        with open(g_nodelstFileName, 'r', newline='') as csvfile, tempfile:
            reader = csv.reader(csvfile)
            writer = csv.writer(tempfile)
            for row in reader:
                if row:
                    if row[0] == queryStr[0] and row[1] == queryStr[1]:
                        print("requested node is already exists")
                        csvfile.close()
                        tempfile.close()
                        return -1
                    else:
                        writer.writerow(row)
            writer.writerows(txDataList)
        shutil.move(tempfile.name, g_nodelstFileName)
        csvfile.close()
        tempfile.close()
    # "nodelst.csv"파일이 존재하지 않는 경우
    except:
        # this is 1st time of creating node list
        try:
            # 쓰기용으로 "nodelst.csv"이름이 파일스트림을 연다. 존재하지 않으면 새로 생성
            with open(g_nodelstFileName, "w", newline='') as file:
                writer = csv.writer(file)
                writer.writerows(txDataList)
        # 파일스트림을 여는데 실패한 경우 return 0
        except:
            return 0

    return 1
    print('new node written to nodelist.csv.')


# g_nodelstFileName, "nodelst.csv"의 내용을 읽어온다.
def readNodes(filePath):
    print("read Nodes")
    importedNodes = []

    try:

        with open(filePath, 'r', newline='') as file:
            txReader = csv.reader(file)

            for row in txReader:
                line = [row[0], row[1]]
                importedNodes.append(line)
        print("Pulling txData from csv...")
        return importedNodes
    except:

        return []

def broadcastNewBlock(blockchain):

    importedNodes = readNodes(g_nodelstFileName)  # get server node ip and port

    reqHeader = {'Content-Type': 'application/json; charset=utf-8'}

    reqBody = []

    for i in blockchain:
       reqBody.append(i.__dict__)

    if len(importedNodes) > 0:
        for node in importedNodes:
            try:

                URL = "http://" + node[0] + ":" + node[
                    1] + g_receiveNewBlock  # 형태 : http://ip:port/node/receiveNewBlock

                res = requests.post(URL, headers=reqHeader, data=json.dumps(reqBody))

                if res.status_code == 200:
                    print(URL + " sent ok.")
                    print("Response Message " + res.text)

                else:
                    print(URL + " responding error " + res.status_code)

            except:
                print(URL + " is not responding.")
                # write responding results

                tempfile = NamedTemporaryFile(mode='w', newline='', delete=False)
                try:

                    # 해당 파일이 존재하지않다면, except로 빠진다.
                    with open(g_nodelstFileName, 'r', newline='') as csvfile, tempfile:
                        reader = csv.reader(csvfile)
                        writer = csv.writer(tempfile)

                        for row in reader:
                            # if row?
                            if row:

                                if row[0] == node[0] and row[1] == node[1]:
                                    print("connection failed " + row[0] + ":" + row[1] + ", number of fail " + row[2])

                                    tmp = row[2]
                                    if int(tmp) > g_maximumTry:
                                        print(row[0] + ":" + row[
                                            1] + " deleted from node list because of exceeding the request limit")

                                    else:

                                        row[2] = int(tmp) + 1
                                        writer.writerow(row)

                                else:
                                    writer.writerow(row)

                    shutil.move(tempfile.name, g_nodelstFileName)

                    csvfile.close()
                    tempfile.close()

                except:
                    print("caught exception while updating node list")


def row_count(filename):
    try:
        with open(filename) as in_file:
            return sum(1 for _ in in_file)
    except:
        return 0

def compareMerge(bcDict):
    heldBlock = []
    bcToValidateForBlock = []

    # Read GenesisBlock
    try:
        with open(g_bcFileName, 'r', newline='') as file:
            blockReader = csv.reader(file)
            # last_line_number = row_count(g_bcFileName)
            for line in blockReader:
                # -----------------------------------------V01 : 완
                # line[6] merkleHash 추가
                block = Block(line[0], line[1], line[2], line[3], line[4], line[5], line[6])
                heldBlock.append(block)
                # if blockReader.line_num == 1:
                #    block = Block(line[0], line[1], line[2], line[3], line[4], line[5])
                #    heldBlock.append(block)
                # elif blockReader.line_num == last_line_number:
                #    block = Block(line[0], line[1], line[2], line[3], line[4], line[5])
                #    heldBlock.append(block)

    except:
        print("file open error in compareMerge or No database exists")
        print("call initSvr if this server has just installed")
        return -1

    # if it fails to read block data  from db(csv)
    if len(heldBlock) == 0:
        print("fail to read")
        return -2

    # transform given data to Block object
    for line in bcDict:
        # print(type(line))
        # index, previousHash, timestamp, data, currentHash, proof
        # Block생성자로 객체를 생성하여 block에 넣는다.
        # -----------------------------------------V01 : 완
        # line['merkleHash'] merkleHash 추가
        block = Block(line['index'], line['previousHash'], line['timestamp'], line['data'], line['currentHash'],
                      line['proof'], line['merkleHash'])
        # block객체형 list 변수에 다시 block객체를 넣는다
        bcToValidateForBlock.append(block)

    # compare the given data with genesisBlock
    if not isSameBlock(bcToValidateForBlock[0], heldBlock[0]):
        print('Genesis Block Incorrect')
        return -1

    # check if broadcasted new block,1 ahead than > last held block

    if isValidNewBlock(bcToValidateForBlock[-1], heldBlock[-1]) == False:

        # latest block == broadcasted last block
        if isSameBlock(heldBlock[-1], bcToValidateForBlock[-1]) == True:
            print('latest block == broadcasted last block, already updated')
            return 2
        # select longest chain
        elif len(bcToValidateForBlock) > len(heldBlock):
            # validation
            if isSameBlock(heldBlock[0], bcToValidateForBlock[0]) == False:
                print("Block Information Incorrect #1")
                return -1
            tempBlocks = [bcToValidateForBlock[0]]
            for i in range(1, len(bcToValidateForBlock)):
                if isValidNewBlock(bcToValidateForBlock[i], tempBlocks[i - 1]):
                    tempBlocks.append(bcToValidateForBlock[i])
                else:
                    return -1
            # [START] save it to csv
            blockchainList = []
            for block in bcToValidateForBlock:
                blockList = [block.index, block.previousHash, str(block.timestamp), block.data,
                             block.currentHash, block.proof]
                blockchainList.append(blockList)
            with open(g_bcFileName, "w", newline='') as file:
                writer = csv.writer(file)
                writer.writerows(blockchainList)
            # [END] save it to csv
            return 1
        elif len(bcToValidateForBlock) < len(heldBlock):
            # validation
            # for i in range(0,len(bcToValidateForBlock)):
            #    if isSameBlock(heldBlock[i], bcToValidateForBlock[i]) == False:
            #        print("Block Information Incorrect #1")
            #        return -1
            tempBlocks = [bcToValidateForBlock[0]]
            for i in range(1, len(bcToValidateForBlock)):
                if isValidNewBlock(bcToValidateForBlock[i], tempBlocks[i - 1]):
                    tempBlocks.append(bcToValidateForBlock[i])
                else:
                    return -1
            print("We have a longer chain")
            return 3
        else:
            print("Block Information Incorrect #2")
            return -1
    else:  # very normal case (ex> we have index 100 and receive index 101 ...)
        tempBlocks = [bcToValidateForBlock[0]]
        for i in range(1, len(bcToValidateForBlock)):
            if isValidNewBlock(bcToValidateForBlock[i], tempBlocks[i - 1]):
                tempBlocks.append(bcToValidateForBlock[i])
            else:
                print("Block Information Incorrect #2 " + tempBlocks.__dict__)
                return -1

        print("new block good")

        # validation
        for i in range(0, len(heldBlock)):
            if isSameBlock(heldBlock[i], bcToValidateForBlock[i]) == False:
                print("Block Information Incorrect #1")
                return -1
        # [START] save it to csv
        blockchainList = []
        for block in bcToValidateForBlock:
            blockList = [block.index, block.previousHash, str(block.timestamp), block.data, block.currentHash,
                         block.proof]
            blockchainList.append(blockList)
        with open(g_bcFileName, "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerows(blockchainList)
        # [END] save it to csv
        return 1


def initSvr():
    print("init Server")
    # 1. check if we have a node list file
    last_line_number = row_count(g_nodelstFileName)
    # if we don't have, let's request node list
    if last_line_number == 0:
        # get nodes...
        for key, value in g_nodeList.items():
            URL = 'http://' + key + ':' + value + '/node/getNode'
            try:
                res = requests.get(URL)
            except requests.exceptions.ConnectionError:
                continue
            if res.status_code == 200:
                print(res.text)
                tmpNodeLists = json.loads(res.text)
                for node in tmpNodeLists:
                    addNode(node)

    # 2. check if we have a blockchain data file
    last_line_number = row_count(g_bcFileName)
    blockchainList = []
    if last_line_number == 0:
        # get Block Data...
        for key, value in g_nodeList.items():
            URL = 'http://' + key + ':' + value + '/block/getBlockData'
            try:
                res = requests.get(URL)
            except requests.exceptions.ConnectionError:
                continue
            if res.status_code == 200:
                print(res.text)
                tmpbcData = json.loads(res.text)
                for line in tmpbcData:
                    # print(type(line))
                    # index, previousHash, timestamp, data, currentHash, proof, merkleHash
                    # -----------------------------------------V01 : 완
                    # line['merkleHash'] merkleHash 추가
                    block = [line['index'], line['previousHash'], line['timestamp'], line['data'], line['currentHash'],
                             line['proof'], line['merkleHash']]
                    blockchainList.append(block)
                try:
                    with open(g_bcFileName, "w", newline='') as file:
                        writer = csv.writer(file)
                        writer.writerows(blockchainList)
                except Exception as e:
                    print("file write error in initSvr() " + e)
    # -----------------------------------------V02 : 완
    # 3. check if we have a txData file
    last_line_number = row_count(g_txFileName)
    txDataList = []
    if last_line_number == 0:
        # get txData...
        for key, value in g_nodeList.items():
            URL = 'http://' + key + ':' + value + '/txData/getTxData'
            try:
                res = requests.get(URL)
            except requests.exceptions.ConnectionError:
                continue
            if res.status_code == 200:
                print(res.text)
                tmpTxData = json.loads(res.text)
                for line in tmpTxData:
                    # print(type(line))
                    # amount, commitYN, fee, receiver, sender, uuid
                    txData = [line['commitYN'],line['receiver'], line['amount'], line['sender'], line['fee'],
                             line['uuid'], line['transactionTime']]
                    txDataList.append(txData)
                try:
                    with open(g_txFileName, "w", newline='') as file:
                        writer = csv.writer(file)
                        writer.writerows(txDataList)
                except Exception as e:
                    print("file write error in initSvr() " + e)

    return 1

# This class will handle any incoming request from
# a browser
class myHandler(BaseHTTPRequestHandler):

    # def __init__(self, request, client_address, server):
    #    BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    # Handler for the GET requests
    # get방식으로 보내는 요청의 종류로는 블록체인의 데이터 요청, 블록 생성, 노드데이터 요청, 노드생성이 존재한다.
    def do_GET(self):
        data = []  # response json data
        if None != re.search('/block/*', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            if None != re.search('/block/getBlockData', self.path):

                block = readBlockchain(g_bcFileName, mode='external')

                # block의 값이 None인 경우
                if block == None:

                    print("No Block Exists")

                    data.append("no data exists")
                else:
                    for i in block:
                        print(i.__dict__)
                        data.append(i.__dict__)

                self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

            # 블럭을 생성하는 경우 (최초, 그 이후 전부)
            elif None != re.search('/block/generateBlock', self.path):

                t = threading.Thread(target=mine)
                t.start()
                data.append("{mining is underway:check later by calling /block/getBlockData}")
                self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))
            else:
                data.append("{info:no such api}")
                self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))


        elif None != re.search('/node/*', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            if None != re.search('/node/addNode', self.path):

                queryStr = urlparse(self.path).query.split(':')
                print("client ip : " + self.client_address[0] + " query ip : " + queryStr[0])

                if self.client_address[0] != queryStr[0]:
                    data.append("your ip address doesn't match with the requested parameter")

                else:
                    res = addNode(queryStr)

                    if res == 1:
                        importedNodes = readNodes(g_nodelstFileName)
                        data = importedNodes
                        print("node added okay")

                    elif res == 0:
                        data.append("caught exception while saving")

                    elif res == -1:
                        importedNodes = readNodes(g_nodelstFileName)
                        data = importedNodes
                        data.append("requested node is already exists")

                self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

            elif None != re.search('/node/getNode', self.path):
                importedNodes = readNodes(g_nodelstFileName)
                data = importedNodes
                self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

        # -----------------------------------------V02 : 완
        # txData 요청에 대한 response 부분 추가. mode=''인 경우는 모든 데이터를 가져온다.
        elif None != re.search('/txData/*', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            if None != re.search('/txData/getTxData', self.path):

                txDataList = readTx(g_txFileName, mode='external')

                if txDataList == '':

                    print("No txData Exists")

                    data.append("no txData exists")
                else:
                    for i in txDataList:
                        print(i.__dict__)
                        data.append(i.__dict__)

                self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))
        else:
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
        # ref : https://mafayyaz.wordpress.com/2013/02/08/writing-simple-http-server-in-python-with-rest-and-json/

    def do_POST(self):

        if None != re.search('/block/*', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            if None != re.search('/block/validateBlock/*', self.path):
                ctype, pdict = cgi.parse_header(self.headers['content-type'])
                # print(ctype) #print(pdict)

                if ctype == 'application/json':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    receivedData = post_data.decode('utf-8')
                    print(type(receivedData))
                    tempDict = json.loads(receivedData)  # load your str into a list #print(type(tempDict))
                    if isValidChain(tempDict) == True:
                        tempDict.append("validationResult:normal")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))
                    else:
                        tempDict.append("validationResult:abnormal")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))

            elif None != re.search('/block/newtx', self.path):
                ctype, pdict = cgi.parse_header(self.headers['content-type'])
                if ctype == 'application/json':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    receivedData = post_data.decode('utf-8')
                    print(type(receivedData))
                    tempDict = json.loads(receivedData)
                    res = newtx(tempDict)
                    if res == 1:
                        tempDict.append("accepted : it will be mined later")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))
                    elif res == -1:
                        tempDict.append("declined : number of request txData exceeds limitation")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))
                    elif res == -2:
                        tempDict.append("declined : error on data read or write")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))
                    else:
                        tempDict.append("error : requested data is abnormal")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))

            # -----------------------------------------V02 : 완
            # "/block/syncTx'" 로 오는 요청은 다시 sync과정을 거치지 않는다.
            elif None != re.search('/block/syncTx', self.path) :
                ctype, pdict = cgi.parse_header(self.headers['content-type'])
                if ctype == 'application/json':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    receivedData = post_data.decode('utf-8')
                    print(type(receivedData))
                    tempDict = json.loads(receivedData)
                    res = newtx(tempDict, mode='sync')

                    if res == 1:
                        tempDict.append("accepted : it will be mined later")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))
                    elif res == -1:
                        tempDict.append("declined : number of request txData exceeds limitation")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))
                    elif res == -2:
                        tempDict.append("declined : error on data read or write")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))
                    else:
                        tempDict.append("error : requested data is abnormal")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))

        elif None != re.search('/node/*', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            if None != re.search(g_receiveNewBlock, self.path):  # /node/receiveNewBlock
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                receivedData = post_data.decode('utf-8')
                tempDict = json.loads(receivedData)  # load your str into a list
                print(tempDict)
                res = compareMerge(tempDict)
                if res == -1:  # internal error
                    tempDict.append("internal server error")
                elif res == -2:  # block chain info incorrect
                    tempDict.append("block chain info incorrect")
                elif res == 1:  # normal
                    tempDict.append("accepted")
                elif res == 2:  # identical
                    tempDict.append("already updated")
                elif res == 3:  # we have a longer chain
                    tempDict.append("we have a longer chain")
                self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))

        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

        return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


try:

    # Create a web server and define the handler to manage the
    # incoming request
    # server = HTTPServer(('', PORT_NUMBER), myHandler)
    server = ThreadedHTTPServer(('', PORT_NUMBER), myHandler)
    print('Started httpserver on port ', PORT_NUMBER)

    initSvr()
    # Wait forever for incoming http requests
    server.serve_forever()

except (KeyboardInterrupt, Exception) as e:
    print('^C received, shutting down the web server')
    print(e)
    server.socket.close()