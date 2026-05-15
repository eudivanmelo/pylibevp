#include <libevp.hpp>

#include <array>
#include <cstdint>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

namespace {
    using native_evp   = libevp::evp;
    using native_fd    = libevp::evp_fd;
    using native_range = std::vector<native_fd>;

    struct c_evp_fd {
        const char* file;
        std::uint32_t data_offset;
        std::uint32_t data_size;
        std::uint32_t data_compressed_size;
        std::uint32_t flags;
        std::uint8_t hash[16];
    };

    struct c_evp_result {
        int status;
        char message[1024];
    };

    static native_evp g_evp;
    static native_range g_last_archive_files;

    static c_evp_result make_result(const libevp::evp_result& result) {
        c_evp_result out{};
        out.status = static_cast<int>(result.status);
        std::strncpy(out.message, result.message.c_str(), sizeof(out.message) - 1);
        out.message[sizeof(out.message) - 1] = '\0';
        return out;
    }

    static char* duplicate_string(const std::string& value) {
        auto* buffer = new char[value.size() + 1];
        std::memcpy(buffer, value.c_str(), value.size() + 1);
        return buffer;
    }

    static std::vector<libevp::DIR_PATH> make_file_list(const char** files, int count) {
        std::vector<libevp::DIR_PATH> output;
        output.reserve(count > 0 ? count : 0);
        for (int i = 0; i < count; ++i) {
            if (files && files[i]) {
                output.emplace_back(files[i]);
            }
        }
        return output;
    }
}

#if defined(_WIN32)
    #define LIBEVP_WRAPPER_API __declspec(dllexport)
#else
    #define LIBEVP_WRAPPER_API
#endif

extern "C" {
    LIBEVP_WRAPPER_API void evp_init() {
        g_last_archive_files.clear();
    }

    LIBEVP_WRAPPER_API void evp_cleanup() {
        g_last_archive_files.clear();
    }

    LIBEVP_WRAPPER_API c_evp_result evp_get_archive_fds(const char* archive_path, c_evp_fd** out_files, int* out_count) {
        if (!archive_path || !out_files || !out_count) {
            c_evp_result result{};
            result.status = static_cast<int>(libevp::evp_result::status::failure);
            std::strncpy(result.message, "invalid arguments", sizeof(result.message) - 1);
            return result;
        }

        g_last_archive_files.clear();
        auto result = g_evp.get_archive_fds(archive_path, g_last_archive_files);
        if (!result) {
            return make_result(result);
        }

        *out_count = static_cast<int>(g_last_archive_files.size());
        if (*out_count == 0) {
            *out_files = nullptr;
            return make_result(result);
        }

        auto* files = new c_evp_fd[*out_count];
        for (int i = 0; i < *out_count; ++i) {
            const auto& src = g_last_archive_files[static_cast<std::size_t>(i)];
            files[i].file = duplicate_string(src.file);
            files[i].data_offset = src.data_offset;
            files[i].data_size = src.data_size;
            files[i].data_compressed_size = src.data_compressed_size;
            files[i].flags = src.flags;
            for (std::size_t j = 0; j < src.hash.size(); ++j) {
                files[i].hash[j] = src.hash[j];
            }
        }

        *out_files = files;
        return make_result(result);
    }

    LIBEVP_WRAPPER_API void evp_free_fds(c_evp_fd* files, int count) {
        if (!files) {
            return;
        }

        for (int i = 0; i < count; ++i) {
            delete[] files[i].file;
        }

        delete[] files;
    }

    LIBEVP_WRAPPER_API c_evp_result evp_unpack(const char* archive_path, const char* output_dir) {
        if (!archive_path || !output_dir) {
            c_evp_result result{};
            result.status = static_cast<int>(libevp::evp_result::status::failure);
            std::strncpy(result.message, "invalid arguments", sizeof(result.message) - 1);
            return result;
        }

        libevp::evp::unpack_input input;
        input.archive = archive_path;

        auto result = g_evp.unpack(input, output_dir);
        return make_result(result);
    }

    LIBEVP_WRAPPER_API c_evp_result evp_pack(const char* base_path, const char** files, int count, const char* output_archive) {
        if (!base_path || !output_archive) {
            c_evp_result result{};
            result.status = static_cast<int>(libevp::evp_result::status::failure);
            std::strncpy(result.message, "invalid arguments", sizeof(result.message) - 1);
            return result;
        }

        libevp::evp::pack_input input;
        input.base = base_path;
        input.files = make_file_list(files, count);

        auto result = g_evp.pack(input, output_archive);
        return make_result(result);
    }

    LIBEVP_WRAPPER_API int evp_get_file_count() {
        return static_cast<int>(g_last_archive_files.size());
    }

    LIBEVP_WRAPPER_API int evp_get_file_info(int index, char* filename_buffer, int buffer_size, std::uint32_t* data_size, std::uint32_t* compressed_size) {
        if (index < 0 || !filename_buffer || buffer_size <= 0 || !data_size || !compressed_size) {
            return -1;
        }

        const auto idx = static_cast<std::size_t>(index);
        if (idx >= g_last_archive_files.size()) {
            return -1;
        }

        const auto& file = g_last_archive_files[idx];
        std::strncpy(filename_buffer, file.file.c_str(), static_cast<std::size_t>(buffer_size) - 1);
        filename_buffer[buffer_size - 1] = '\0';
        *data_size = file.data_size;
        *compressed_size = file.data_compressed_size;
        return 0;
    }
}