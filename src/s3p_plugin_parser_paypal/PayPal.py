import datetime
import time
import dateparser
from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument, S3PPlugin
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class PayPal(S3PParserBase):
    """
    A Parser payload that uses S3P Parser base class.
    """
    HOST = "https://newsroom.paypal-corp.com/news"

    def __init__(self, refer: S3PRefer, plugin: S3PPlugin, web_driver: WebDriver, max_count_documents: int = None,
                 last_document: S3PDocument = None):
        super().__init__(refer, plugin, max_count_documents, last_document)

        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self._driver = web_driver
        self._wait = WebDriverWait(self._driver, timeout=20)

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -

        self._driver.get(self.HOST)  # Открыть первую страницу с материалами
        time.sleep(5)

        # Окно с куками пропадает самостоятельно через 2-3 секунды
        try:
            cookies_btn = self._driver.find_element(By.ID, 'acceptAllButton').find_element(By.XPATH,
                                                                                           '//*[@id="acceptAllButton"]')
            self._driver.execute_script('arguments[0].click()', cookies_btn)
            self.logger.debug('Cookies убран')
        except:
            self.logger.exception('Не найден cookies')
            pass

        # self.logger.info('Прекращен поиск Cookies')
        # time.sleep(3)
        counter = 0
        flag = True
        while flag:

            self.logger.debug('Загрузка списка элементов...')
            doc_table = self._driver.find_element(By.CLASS_NAME, 'wd_item_list').find_elements(By.CLASS_NAME,
                                                                                               'wd_has-image')
            self.logger.debug('Обработка списка элементов...')

            # Цикл по всем строкам таблицы элементов на текущей странице
            for element in doc_table:

                element_locked = False

                try:
                    title = element.find_element(By.CLASS_NAME, 'wd_title').text
                    # title = element.find_element(By.XPATH, '//*[@id="feed-item-title-1"]/a').text

                except:
                    self.logger.exception('Не удалось извлечь title')
                    title = ' '

                # try:
                #    other_data = element.find_elements(By.CLASS_NAME, "wd_category_link_list").text
                # except:
                #    self.logger.exception('Не удалось извлечь other_data')
                #    other_data = ''
                # // *[ @ id = "main-content"] / ul / li[1] / div[2] / span[2]
                # // *[ @ id = "main-content"] / ul / li[2] / div[2] / span[2]

                try:
                    date = dateparser.parse(element.find_element(By.CLASS_NAME, 'wd_date').text)
                except:
                    self.logger.exception('Не удалось извлечь date_text')
                    date = None
                    continue

                # try:
                #    date = dateparser.parse(date_text)
                # except:
                #    self.logger.exception('Не удалось извлечь date')
                #    date = None

                try:
                    abstract = element.find_element(By.CLASS_NAME, 'wd_summary').text
                except:
                    self.logger.exception('Не удалось извлечь abstract')
                    abstract = ''

                try:
                    web_link = element.find_element(By.TAG_NAME, 'a').get_attribute('href')
                except:
                    self.logger.exception('Не удалось извлечь web_link')
                    web_link = None
                    continue

                self._driver.execute_script("window.open('');")
                self._driver.switch_to.window(self._driver.window_handles[1])
                self._driver.get(web_link)
                self._wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.wd_news_body')))

                text_content = self._driver.find_element(By.CLASS_NAME, 'wd_news_body').text

                cats = [x.text for x in self._driver.find_elements(By.CLASS_NAME, 'wd_category_link')]

                other_data = {'categories': cats}

                doc = S3PDocument(
                    id=None,
                    title=title,
                    abstract=abstract,
                    text=text_content,
                    link=web_link,
                    storage=None,
                    other=other_data,
                    published=date,
                    loaded=datetime.datetime.now(),
                )

                self._find(doc)

                self._driver.close()
                self._driver.switch_to.window(self._driver.window_handles[0])

            try:
                pagination_arrow = self._driver.find_element(By.XPATH, '//li[contains(@class, \'wd_page_next\')]')
                self._driver.execute_script('arguments[0].click()', pagination_arrow)
                # pagination_arrow.click()
                time.sleep(3)
                # pg_num = self._driver.find_element(By.ID, 'current_page').text
                self.logger.debug(f'Выполнен переход на след. страницу')

                # if int(pg_num) > 3:
                #    self.logger.info('Выполнен переход на 4-ую страницу. Принудительное завершение парсинга.')
                # break

            except:
                self.logger.exception('Не удалось найти переход на след. страницу. Прерывание цикла обработки')
                break

        # Логирование найденного документа
        # self.logger.info(self._find_document_text_for_logger(_content_document))

        # ---
        # ========================================
