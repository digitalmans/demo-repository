package com.hackathon.moodpixel.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Base64;

/**
 * Agnes AI image API: OpenAI-style POST /v1/images/generations.
 */
@Service
public class AgnesImageService {

    private static final Logger log = LoggerFactory.getLogger(AgnesImageService.class);
    private static final int PROMPT_MAX_LEN = 1500;

    private static final String CARTOON_PORTRAIT_PROMPT = String.join(" ",
            "Transform the uploaded portrait into a super cute chibi cartoon illustration.",
            "Strictly preserve the subject identity, hairstyle, hair color, clothing style, main colors, pose, and composition.",
            "Use a big-head-small-body proportion, rounded facial features, simplified details, flat saturated colors, soft clean outlines.",
            "Use a simple clean background. Do not turn it into a realistic photo. Do not change to a different person.",
            "Make the result suitable as a perler bead / pixel art source image.");

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(30))
            .build();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${agnes.api-key:}")
    private String apiKey;

    @Value("${agnes.api-base:https://apihub.agnes-ai.com/v1}")
    private String apiBase;

    @Value("${agnes.image-model:agnes-image-2.1-flash}")
    private String imageModel;

    @Value("${agnes.image-size:1024x1024}")
    private String imageSize;

    public byte[] generateMoodImageBytes(String userText) throws Exception {
        ensureApiKey();
        String prompt = truncate(buildMoodPrompt(userText), PROMPT_MAX_LEN);

        ObjectNode body = objectMapper.createObjectNode();
        body.put("model", imageModel);
        body.put("prompt", prompt);
        body.put("size", imageSize);
        body.put("return_base64", true);

        log.info("[Agnes] 文生图 model={} size={} promptLen={} promptPreview={}",
                imageModel, imageSize, prompt.length(), preview(prompt, 120));
        return postImageGeneration(body);
    }

    public byte[] generateCartoonFromPortrait(byte[] imageBytes, String mimeType) throws Exception {
        ensureApiKey();
        if (imageBytes == null || imageBytes.length == 0) {
            throw new IllegalStateException("图片数据为空");
        }
        if (imageBytes.length > 10 * 1024 * 1024) {
            throw new IllegalStateException("图片需小于 10MB");
        }

        String dataUrlMime = normalizeDataUrlMime(mimeType);
        String dataUrl = "data:" + dataUrlMime + ";base64," + Base64.getEncoder().encodeToString(imageBytes);
        String size = outputSizeForInput(imageBytes);

        ObjectNode body = objectMapper.createObjectNode();
        body.put("model", imageModel);
        body.put("prompt", CARTOON_PORTRAIT_PROMPT);
        body.put("size", size);

        ObjectNode extraBody = objectMapper.createObjectNode();
        ArrayNode images = objectMapper.createArrayNode();
        images.add(dataUrl);
        extraBody.set("image", images);
        extraBody.put("response_format", "b64_json");
        body.set("extra_body", extraBody);

        log.info("[Agnes] 图生图卡通化 model={} size={} refBytes={} mime={}",
                imageModel, size, imageBytes.length, dataUrlMime);
        return postImageGeneration(body);
    }

    private byte[] postImageGeneration(ObjectNode body) throws Exception {
        String json = objectMapper.writeValueAsString(body);
        String url = combineUrl(apiBase, "/images/generations");
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofMinutes(6))
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + apiKey.trim())
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .header(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
                .POST(HttpRequest.BodyPublishers.ofString(json, StandardCharsets.UTF_8))
                .build();

        long start = System.nanoTime();
        HttpResponse<String> response;
        try {
            response = httpClient.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("调用 Agnes 时被中断，请重试", e);
        } catch (IOException e) {
            log.error("Agnes 网络错误: {}", e.toString());
            throw new IllegalStateException("无法连接 Agnes 或网络异常: " + describeIo(e), e);
        }

        log.info("[Agnes] HTTP status={} bodyLen={} 耗时 {} ms",
                response.statusCode(),
                response.body() != null ? response.body().length() : 0,
                (System.nanoTime() - start) / 1_000_000L);

        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            throw new IllegalStateException("Agnes 接口 HTTP " + response.statusCode() + ": "
                    + preview(response.body(), 800));
        }

        JsonNode root = objectMapper.readTree(response.body());
        JsonNode data = root.path("data");
        if (!data.isArray() || data.isEmpty()) {
            throw new IllegalStateException("Agnes 未返回 data: " + preview(response.body(), 800));
        }

        JsonNode first = data.get(0);
        String b64 = first.path("b64_json").asText("");
        if (!b64.isBlank()) {
            try {
                return Base64.getDecoder().decode(stripDataUrlBase64(b64));
            } catch (IllegalArgumentException e) {
                throw new IllegalStateException("Agnes 返回的 Base64 无法解码", e);
            }
        }

        String imageUrl = first.path("url").asText("");
        if (!imageUrl.isBlank()) {
            return downloadImage(imageUrl);
        }

        throw new IllegalStateException("Agnes 响应中没有 b64_json 或 url: " + preview(response.body(), 800));
    }

    private byte[] downloadImage(String imageUrl) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(imageUrl))
                .timeout(Duration.ofMinutes(2))
                .GET()
                .build();
        HttpResponse<byte[]> response = httpClient.send(request, HttpResponse.BodyHandlers.ofByteArray());
        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            throw new IllegalStateException("下载 Agnes 生成图失败 HTTP " + response.statusCode());
        }
        byte[] body = response.body();
        if (body == null || body.length == 0) {
            throw new IllegalStateException("下载 Agnes 生成图为空");
        }
        return body;
    }

    private void ensureApiKey() {
        if (apiKey == null || apiKey.isBlank()) {
            throw new IllegalStateException("未配置 Agnes API Key，请设置环境变量 AGNES_API_KEY 或 agnes.api-key");
        }
    }

    private static String outputSizeForInput(byte[] imageBytes) {
        int[] wh = readImageWidthHeight(imageBytes);
        if (wh == null || wh[0] <= 0 || wh[1] <= 0) {
            return "1024x1024";
        }
        double ratio = (double) wh[0] / (double) wh[1];
        if (ratio > 1.2) {
            return "1024x768";
        }
        if (ratio < 0.83) {
            return "768x1024";
        }
        return "1024x1024";
    }

    static String normalizeDataUrlMime(String mimeType) {
        if (mimeType == null || mimeType.isBlank()) {
            return "image/jpeg";
        }
        String m = mimeType.split(";")[0].trim().toLowerCase();
        if (m.equals("image/jpg")) {
            return "image/jpeg";
        }
        if (m.equals("image/jpeg") || m.equals("image/png")) {
            return m;
        }
        throw new IllegalStateException("仅支持 JPEG 或 PNG 作为参考图");
    }

    static int[] readImageWidthHeight(byte[] imageBytes) {
        if (imageBytes == null || imageBytes.length == 0) {
            return null;
        }
        try {
            BufferedImage image = ImageIO.read(new ByteArrayInputStream(imageBytes));
            if (image == null) {
                return null;
            }
            return new int[] {image.getWidth(), image.getHeight()};
        } catch (IOException e) {
            log.warn("读取图片宽高失败: {}", describeIo(e));
            return null;
        }
    }

    static String buildMoodPrompt(String userText) {
        String t = userText == null ? "" : userText.trim();
        if (t.isEmpty()) {
            t = "平静与期待";
        }
        return """
                Create a single striking artistic image that visually expresses the emotional mood and inner feeling described below.
                Style: expressive, atmospheric, symbolic, cute perler bead pixel art source image.
                No text, no letters, no watermark. Square composition, rich mood, clean subject, suitable for pixelation.

                Author's words and mood to express:
                """ + t;
    }

    static String combineUrl(String base, String path) {
        String b = (base == null || base.isBlank()) ? "https://apihub.agnes-ai.com/v1" : base.trim();
        b = b.endsWith("/") ? b.substring(0, b.length() - 1) : b;
        String p = path.startsWith("/") ? path : "/" + path;
        return b + p;
    }

    static String truncate(String s, int max) {
        if (s == null) {
            return "";
        }
        return s.length() <= max ? s : s.substring(0, max);
    }

    static String preview(String s, int max) {
        if (s == null) {
            return "null";
        }
        String t = s.replace("\r", " ").replace("\n", " ");
        return t.length() <= max ? t : t.substring(0, max) + "...";
    }

    static String stripDataUrlBase64(String raw) {
        String s = raw.trim();
        int i = s.indexOf("base64,");
        if (i >= 0) {
            return s.substring(i + "base64,".length()).trim();
        }
        return s;
    }

    static String describeIo(IOException e) {
        String m = e.getMessage();
        return (m != null && !m.isBlank()) ? m : e.getClass().getSimpleName();
    }
}
